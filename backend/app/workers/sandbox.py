"""Sandbox adapter used by the run/judge workers.

Uses a Docker-isolated container when Docker is available (production/CI —
see docker/runners/ for the images). Falls back to running the submitted
source directly on the host, bounded only by a subprocess timeout, when
Docker is absent. That fallback exists so local development works without a
Docker install; it is NOT isolated (no network/filesystem/memory limits) and
must never be used for untrusted, multi-user submissions.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core import languages
from app.core.languages import Language

# Kept as a mapping so callers can test membership; the runner facts themselves
# live in the language registry.
SPECS = languages.LANGUAGES

logger = logging.getLogger(__name__)

_DOCKER = shutil.which("docker")
if not _DOCKER:
    logger.warning(
        "Docker not found on PATH; submitted code will run directly on this host "
        "with no sandboxing (local-dev fallback only — never use for untrusted "
        "submissions)."
    )


@dataclass(frozen=True)
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool = False


def run_source(
    language: str, source_code: str, stdin: str, timeout_seconds: float, memory_mb: int
) -> SandboxResult:
    """Run one source file in a resource-constrained, networkless container.

    Falls back to unsandboxed local execution when Docker isn't installed
    (``memory_mb`` is then advisory only — it can't be enforced without cgroups).
    """
    spec = languages.get(language)
    with tempfile.TemporaryDirectory(prefix="codeforge-exec-") as directory:
        source_path = Path(directory, spec.source_filename)
        source_path.write_text(source_code, encoding="utf-8")
        if _DOCKER:
            return _run_in_docker(spec, directory, stdin, timeout_seconds, memory_mb)
        return _run_locally(spec, directory, source_path, stdin, timeout_seconds)


def _run_in_docker(
    spec: Language, directory: str, stdin: str, timeout_seconds: float, memory_mb: int
) -> SandboxResult:
    try:
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "64",
                "--memory",
                f"{memory_mb}m",
                "--cpus",
                "0.5",
                "--user",
                "10001:10001",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=64m",
                "-v",
                f"{directory}:/workspace:ro",
                "-i",
                spec.image,
                *spec.command,
            ],
            input=stdin,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        return SandboxResult(result.stdout[:65536], result.stderr[:65536], result.returncode)
    except subprocess.TimeoutExpired as exc:
        return _timeout_result(exc)


def _run_locally(
    spec: Language, directory: str, source_path: Path, stdin: str, timeout_seconds: float
) -> SandboxResult:
    try:
        if spec.id == "python":
            return _exec([sys.executable, str(source_path)], stdin, timeout_seconds)
        if spec.id == "javascript":
            return _exec(["node", str(source_path)], stdin, timeout_seconds)
        if spec.id == "c":
            return _compile_and_run(
                ["gcc", "-O2", "-std=c17", "-o", _binary_path(directory), str(source_path), "-lm"],
                directory,
                stdin,
                timeout_seconds,
            )
        if spec.id == "cpp":
            return _compile_and_run(
                ["g++", "-O2", "-std=c++17", "-o", _binary_path(directory), str(source_path)],
                directory,
                stdin,
                timeout_seconds,
            )
        if spec.id == "java":
            compiled = subprocess.run(
                ["javac", "-d", directory, str(source_path)],
                capture_output=True,
                text=True,
                timeout=max(timeout_seconds, 10),
                check=False,
            )
            if compiled.returncode != 0:
                return SandboxResult(
                    compiled.stdout[:65536], compiled.stderr[:65536], compiled.returncode
                )
            return _exec(["java", "-cp", directory, "Main"], stdin, timeout_seconds)
        raise ValueError(f"No local runner registered for language {spec.id!r}.")
    except subprocess.TimeoutExpired as exc:
        return _timeout_result(exc)


def _binary_path(directory: str) -> str:
    return str(Path(directory, "main.exe" if os.name == "nt" else "main"))


def _compile_and_run(
    compile_argv: list[str], directory: str, stdin: str, timeout_seconds: float
) -> SandboxResult:
    compiled = subprocess.run(
        compile_argv,
        capture_output=True,
        text=True,
        timeout=max(timeout_seconds, 10),
        check=False,
    )
    if compiled.returncode != 0:
        return SandboxResult(compiled.stdout[:65536], compiled.stderr[:65536], compiled.returncode)
    return _exec([_binary_path(directory)], stdin, timeout_seconds)


def _exec(argv: list[str], stdin: str, timeout_seconds: float) -> SandboxResult:
    result = subprocess.run(
        argv, input=stdin, text=True, capture_output=True, timeout=timeout_seconds, check=False
    )
    return SandboxResult(result.stdout[:65536], result.stderr[:65536], result.returncode)


def _timeout_result(exc: subprocess.TimeoutExpired) -> SandboxResult:
    stdout_str = (
        exc.stdout.decode("utf-8", errors="replace")
        if isinstance(exc.stdout, bytes)
        else str(exc.stdout or "")
    )
    stderr_str = (
        exc.stderr.decode("utf-8", errors="replace")
        if isinstance(exc.stderr, bytes)
        else str(exc.stderr or "")
    )
    return SandboxResult(stdout_str[:65536], stderr_str[:65536], None, True)
