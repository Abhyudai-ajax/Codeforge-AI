"""What the sandbox actually asks Docker to do.

These tests run no containers. They assert the argv `run_source` builds, which
is the part that decides both correctness (right compiler, right filename) and
containment (no network, no root, bounded resources) for untrusted code.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.core import languages
from app.workers import sandbox


@pytest.fixture()
def captured(monkeypatch):
    """Capture the docker argv and the source file written to the mount."""
    recorded: dict = {}

    def fake_run(argv, **kwargs):
        recorded["argv"] = argv
        recorded["stdin"] = kwargs.get("input")
        recorded["timeout"] = kwargs.get("timeout")
        mount = next(argv[index + 1] for index, item in enumerate(argv) if item == "-v")
        # Split off the mount target rather than on ":" — Windows host paths
        # contain a drive letter.
        host_dir = mount.rsplit(":/workspace", 1)[0]
        recorded["files"] = {
            path.name: path.read_text(encoding="utf-8") for path in Path(host_dir).iterdir()
        }
        return subprocess.CompletedProcess(argv, 0, "ok\n", "")

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)
    return recorded


def test_c_uses_gcc_and_a_dot_c_file(captured):
    result = sandbox.run_source("c", "int main(void){return 0;}", "", 2.0, 128)

    assert result.exit_code == 0
    command = " ".join(captured["argv"])
    assert "codeforge-runner-c:latest" in command
    assert "gcc" in command and "-std=c17" in command
    assert "main.c" in captured["files"]
    assert "main.cpp" not in captured["files"]


def test_cpp_uses_gpp_and_a_dot_cpp_file(captured):
    sandbox.run_source("cpp", "int main(){return 0;}", "", 2.0, 128)

    command = " ".join(captured["argv"])
    assert "codeforge-runner-cpp:latest" in command
    assert "g++" in command and "-std=c++17" in command
    assert "main.cpp" in captured["files"]
    assert "main.c" not in captured["files"]


def test_java_entrypoint_file_is_named_main(captured):
    sandbox.run_source("java", "public class Main {}", "", 2.0, 128)
    assert "Main.java" in captured["files"]


def test_stdin_and_limits_are_forwarded(captured):
    sandbox.run_source("python", "print(1)", "5 7\n", 3.5, 512)

    assert captured["stdin"] == "5 7\n"
    assert captured["timeout"] == 3.5
    argv = captured["argv"]
    assert argv[argv.index("--memory") + 1] == "512m"


@pytest.mark.parametrize("language", sorted(languages.LANGUAGE_IDS))
def test_every_language_runs_with_the_same_containment_flags(language, captured):
    sandbox.run_source(language, "x", "", 1.0, 64)
    argv = captured["argv"]

    assert argv[argv.index("--network") + 1] == "none", "sandbox must have no network"
    assert argv[argv.index("--cap-drop") + 1] == "ALL"
    assert argv[argv.index("--security-opt") + 1] == "no-new-privileges"
    assert argv[argv.index("--user") + 1] == "10001:10001", "must not run as root"
    assert "--read-only" in argv
    assert argv[argv.index("--pids-limit") + 1] == "64"
    # The source mount is read-only so user code cannot rewrite its own input.
    assert argv[argv.index("-v") + 1].endswith(":/workspace:ro")


def test_source_directory_is_removed_after_the_run(captured):
    sandbox.run_source("c", "int main(void){return 0;}", "", 1.0, 64)
    mount = next(
        captured["argv"][index + 1] for index, item in enumerate(captured["argv"]) if item == "-v"
    )
    host_dir = Path(mount.rsplit(":/workspace", 1)[0])
    assert not host_dir.exists(), "temporary source directory must not outlive the run"


def test_timeout_is_reported_rather_than_raised(monkeypatch):
    def fake_run(argv, **kwargs):
        raise subprocess.TimeoutExpired(
            argv, kwargs.get("timeout", 1), output=b"partial", stderr=b""
        )

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)
    result = sandbox.run_source("cpp", "int main(){for(;;);}", "", 1.0, 64)

    assert result.timed_out is True
    assert result.exit_code is None
    assert result.stdout == "partial"
