"""Canonical registry of the languages CodeForge can edit, run, and judge.

Every component that needs to know about a language — the Docker sandbox, the
execution service, the judge workers, the editor metadata endpoint and the
problem seeder — reads it from here, so adding a language is a single edit.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class Language:
    """Everything the platform needs to know about one supported language."""

    id: str
    label: str
    monaco_id: str
    """Syntax mode identifier the Monaco editor expects on the frontend."""
    file_extension: str
    source_filename: str
    """Filename the sandbox writes the submitted source to inside /workspace."""
    image: str
    command: tuple[str, ...]
    """Argv executed inside the runner container."""
    compiled: bool
    """Compiled languages report build failures as compilation errors."""
    comment_prefix: str
    starter_template: str
    """Scaffold shown in the editor. ``{header}`` receives the problem's I/O spec."""


_PYTHON_STARTER = """import sys

{header}


def main() -> None:
    data = sys.stdin.read()
    tokens = data.split()
    # TODO: parse the input above and print the answer.


if __name__ == "__main__":
    main()
"""

_JAVASCRIPT_STARTER = """const data = require('fs').readFileSync(0, 'utf8');
const tokens = data.split(/\\s+/).filter(Boolean);

{header}

// TODO: parse the input above and print the answer.
"""

_C_STARTER = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

{header}

int main(void) {{
    /* TODO: read the input above with scanf/fgets and print the answer. */
    return 0;
}}
"""

_CPP_STARTER = """#include <algorithm>
#include <iostream>
#include <string>
#include <vector>
using namespace std;

{header}

int main() {{
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    // TODO: parse the input above and print the answer.
    return 0;
}}
"""

_JAVA_STARTER = """import java.io.*;
import java.util.*;

{header}

public class Main {{
    public static void main(String[] args) throws IOException {{
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
        // TODO: parse the input above and print the answer.
    }}
}}
"""


_LANGUAGES: tuple[Language, ...] = (
    Language(
        id="python",
        label="Python 3.12",
        monaco_id="python",
        file_extension=".py",
        source_filename="main.py",
        image="codeforge-runner-python:latest",
        command=("python", "/workspace/main.py"),
        compiled=False,
        comment_prefix="# ",
        starter_template=_PYTHON_STARTER,
    ),
    Language(
        id="c",
        label="C (GCC, C17)",
        monaco_id="c",
        file_extension=".c",
        source_filename="main.c",
        image="codeforge-runner-c:latest",
        command=(
            "sh",
            "-c",
            "gcc -O2 -std=c17 -o /tmp/main /workspace/main.c -lm && exec /tmp/main",
        ),
        compiled=True,
        comment_prefix="// ",
        starter_template=_C_STARTER,
    ),
    Language(
        id="cpp",
        label="C++ (GCC, C++17)",
        monaco_id="cpp",
        file_extension=".cpp",
        source_filename="main.cpp",
        image="codeforge-runner-cpp:latest",
        command=(
            "sh",
            "-c",
            "g++ -O2 -std=c++17 -o /tmp/main /workspace/main.cpp && exec /tmp/main",
        ),
        compiled=True,
        comment_prefix="// ",
        starter_template=_CPP_STARTER,
    ),
    Language(
        id="javascript",
        label="JavaScript (Node 22)",
        monaco_id="javascript",
        file_extension=".js",
        source_filename="main.js",
        image="codeforge-runner-javascript:latest",
        command=("node", "/workspace/main.js"),
        compiled=False,
        comment_prefix="// ",
        starter_template=_JAVASCRIPT_STARTER,
    ),
    Language(
        id="java",
        label="Java (Temurin 21)",
        monaco_id="java",
        file_extension=".java",
        source_filename="Main.java",
        image="codeforge-runner-java:latest",
        command=(
            "sh",
            "-c",
            "javac -d /tmp /workspace/Main.java && exec java -cp /tmp Main",
        ),
        compiled=True,
        comment_prefix="// ",
        starter_template=_JAVA_STARTER,
    ),
)

LANGUAGES: MappingProxyType[str, Language] = MappingProxyType(
    {language.id: language for language in _LANGUAGES}
)

LANGUAGE_IDS: tuple[str, ...] = tuple(LANGUAGES)
DEFAULT_LANGUAGE = "python"


def normalize(language: str) -> str:
    """Map user-supplied aliases onto canonical language ids."""
    key = language.strip().lower()
    return _ALIASES.get(key, key)


_ALIASES = {
    "c++": "cpp",
    "cxx": "cpp",
    "c99": "c",
    "c17": "c",
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "py": "python",
    "python3": "python",
}


def is_supported(language: str) -> bool:
    return normalize(language) in LANGUAGES


def get(language: str) -> Language:
    """Return the registry entry, raising ``KeyError`` for unknown languages."""
    return LANGUAGES[normalize(language)]


def is_compiled(language: str) -> bool:
    entry = LANGUAGES.get(normalize(language))
    return bool(entry and entry.compiled)


def starter_code(language: str, header_lines: list[str]) -> str:
    """Render the editor scaffold with the problem's I/O contract as a comment."""
    entry = get(language)
    header = "\n".join(f"{entry.comment_prefix}{line}".rstrip() for line in header_lines)
    return entry.starter_template.format(header=header)


def starter_code_for_all(header_lines: list[str]) -> dict[str, str]:
    """Build the ``starter_code`` map a problem exposes to the editor."""
    return {language_id: starter_code(language_id, header_lines) for language_id in LANGUAGE_IDS}
