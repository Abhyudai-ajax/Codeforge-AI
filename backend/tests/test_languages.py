"""Tests for the language registry and the editor-facing catalog endpoint."""

from __future__ import annotations

import pytest

from app.core import languages
from app.workers.execution import terminal_status
from app.workers.sandbox import SPECS
from app.workers.submission import _failure_status

REQUIRED_LANGUAGES = {"python", "c", "cpp", "javascript", "java"}


def test_registry_covers_the_advertised_languages():
    assert REQUIRED_LANGUAGES <= set(languages.LANGUAGE_IDS)


def test_c_and_cpp_are_compiled_with_distinct_toolchains():
    c_spec = languages.get("c")
    cpp_spec = languages.get("cpp")
    assert c_spec.compiled and cpp_spec.compiled
    assert c_spec.image != cpp_spec.image
    assert c_spec.source_filename == "main.c"
    assert cpp_spec.source_filename == "main.cpp"
    assert "gcc" in " ".join(c_spec.command)
    assert "g++" in " ".join(cpp_spec.command)


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("C", "c"),
        ("C++", "cpp"),
        ("cpp", "cpp"),
        ("  Python  ", "python"),
        ("js", "javascript"),
        ("NodeJS", "javascript"),
    ],
)
def test_aliases_normalize_to_canonical_ids(alias: str, canonical: str):
    assert languages.normalize(alias) == canonical
    assert languages.is_supported(alias)


def test_unknown_language_is_rejected():
    assert not languages.is_supported("brainfuck")
    with pytest.raises(KeyError):
        languages.get("brainfuck")


def test_sandbox_specs_track_the_registry():
    """The sandbox must be able to run everything the registry advertises."""
    assert set(SPECS) == set(languages.LANGUAGE_IDS)


@pytest.mark.parametrize("language", ["c", "cpp", "java"])
def test_compiled_languages_report_compilation_errors(language: str):
    assert languages.is_compiled(language)
    assert terminal_status(language, 1).value == "compilation_error"
    assert _failure_status(language, "syntax error").value == "compilation_error"


@pytest.mark.parametrize("language", ["python", "javascript"])
def test_interpreted_languages_report_runtime_errors(language: str):
    assert not languages.is_compiled(language)
    assert terminal_status(language, 1).value == "runtime_error"
    assert _failure_status(language, "traceback").value == "runtime_error"


def test_starter_code_renders_the_problem_header_per_language():
    starters = languages.starter_code_for_all(["Line 1: n.", "Line 2: n integers."])
    assert set(starters) == set(languages.LANGUAGE_IDS)
    assert "# Line 1: n." in starters["python"]
    assert "// Line 1: n." in starters["c"]
    assert "// Line 1: n." in starters["cpp"]
    for code in starters.values():
        assert "{header}" not in code


@pytest.mark.asyncio
async def test_languages_endpoint_lists_c_and_cpp(client):
    response = await client.get("/api/v1/languages")
    assert response.status_code == 200
    payload = response.json()
    by_id = {entry["id"]: entry for entry in payload}
    assert REQUIRED_LANGUAGES <= set(by_id)
    assert by_id["c"]["monaco_id"] == "c"
    assert by_id["cpp"]["monaco_id"] == "cpp"
    assert by_id["c"]["compiled"] is True
    assert by_id["python"]["is_default"] is True
    assert all(entry["starter_code"].strip() for entry in payload)
