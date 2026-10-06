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
from dataclasses import dataclass, replace
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


_STARTUP_ALLOWANCE_SECONDS = 1.5


def warm_up() -> None:
    """Load the local interpreters once so the first real run isn't a cold start."""
    if _DOCKER:
        return
    for language, source in (("python", "pass\n"), ("javascript", "\n")):
        try:
            run_source(language, source, "", 15, 128)
        except Exception:
            logger.debug("Warm-up for %s skipped.", language, exc_info=True)


@dataclass(frozen=True)
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool = False
    compile_failed: bool = False
    """True when the source never ran because the compiler (or parser) rejected it."""


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
            result = _run_in_docker(spec, directory, stdin, timeout_seconds, memory_mb)
        else:
            result = _run_locally(spec, directory, source_path, stdin, timeout_seconds)
        return _clean_diagnostics(result, directory)


def _clean_diagnostics(result: SandboxResult, directory: str) -> SandboxResult:
    """Make stderr read like the user's file (`main.py:3`) and flag parse errors."""
    stderr = result.stderr
    for prefix in {directory, str(Path(directory).resolve()), "/workspace"}:
        for separator in ("\\", "/"):
            stderr = stderr.replace(prefix + separator, "")
    lines = [
        line
        for line in stderr.splitlines()
        if not (line.strip().startswith("at ") and "node:internal" in line)
        and not line.startswith("Node.js v")
    ]
    stderr = "\n".join(lines).strip()
    # A file Node can't parse fails before any frame inside the user's code runs.
    node_parse_error = any(line.startswith("SyntaxError") for line in lines) and not any(
        line.strip().startswith("at ") and "main.js:" in line for line in lines
    )
    if node_parse_error or _is_python_syntax_error(stderr):
        return replace(result, stderr=stderr, compile_failed=True)
    return replace(result, stderr=stderr)


def _is_python_syntax_error(stderr: str) -> bool:
    last_line = stderr.splitlines()[-1] if stderr else ""
    return last_line.startswith(("SyntaxError", "IndentationError", "TabError"))


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
        # The container compiles and runs in one command, so a compiled language's
        # failure can't be attributed to either phase; report it as a build error.
        return SandboxResult(
            result.stdout[:65536],
            result.stderr[:65536],
            result.returncode,
            compile_failed=spec.compiled and result.returncode != 0,
        )
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
                    compiled.stdout[:65536],
                    compiled.stderr[:65536],
                    compiled.returncode,
                    compile_failed=True,
                )
            return _exec(["java", "-cp", directory, "Main"], stdin, timeout_seconds)
        raise ValueError(f"No local runner registered for language {spec.id!r}.")
    except subprocess.TimeoutExpired as exc:
        return _timeout_result(exc)
    except FileNotFoundError as exc:
        # The toolchain for this language isn't installed on the host.
        missing = Path(exc.filename).name if exc.filename else "the required toolchain"
        return SandboxResult(
            "", f"{spec.label} is not available on this server: {missing} not found on PATH.", 127
        )


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
        return SandboxResult(
            compiled.stdout[:65536],
            compiled.stderr[:65536],
            compiled.returncode,
            compile_failed=True,
        )
    return _exec([_binary_path(directory)], stdin, timeout_seconds)


def _exec(argv: list[str], stdin: str, timeout_seconds: float) -> SandboxResult:
    # Process start-up (interpreter load, antivirus scan of the fresh file) is
    # wall-clock time the program didn't spend running; don't charge it as TLE.
    result = subprocess.run(
        argv,
        input=stdin,
        text=True,
        capture_output=True,
        timeout=timeout_seconds + _STARTUP_ALLOWANCE_SECONDS,
        check=False,
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
