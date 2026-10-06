"""The offline AI fallback must answer about the code it was given, not canned text."""

from __future__ import annotations

import shutil

import pytest

from app.ai.offline_analyzer import analyze, detect_language
from app.db.problem_catalog import CATALOG
from app.workers.sandbox import run_source
from app.workers.submission import _failure_status


def test_prose_is_not_treated_as_code():
    result = analyze("debug", "hi im abhy")
    assert "doesn't look like code" in result
    assert "hi im abhy" in result


def test_python_syntax_error_quotes_the_offending_line():
    code = "import sys\n\n\ndef main() -> Nonejj\n    pass\n"
    result = analyze("debug", code)
    assert "Line 4" in result
    assert "SyntaxError: expected ':'" in result
    assert "def main() -> Nonejj" in result


def test_review_reports_concrete_bugs_with_line_numbers():
    code = (
        "def pick(nums, seen={}):\n"
        "    try:\n"
        "        return nums[len(nums)/2]\n"
        "    except:\n"
        "        return None\n"
    )
    result = analyze("review", code)
    assert "mutable default" in result
    assert "Line 3: Index uses `/`" in result
    assert "Line 4: Bare `except:`" in result


def test_explain_reports_nested_loop_complexity():
    code = "def f(a):\n    for x in a:\n        for y in a:\n            print(x, y)\n\nf([1])\n"
    assert "O(n²)" in analyze("explain", code)


def test_tests_mode_targets_the_real_function_names():
    code = "def add_numbers(a, b):\n    return a + b\n"
    result = analyze("tests", code)
    assert "from solution import add_numbers" in result
    assert "def test_add_numbers_typical_case" in result


def test_hint_uses_the_problem_topic():
    result = analyze("hint", "", "Problem: Daily Temperatures (medium)\nTags: stack\n")
    assert "Daily Temperatures" in result
    assert "stack" in result


@pytest.mark.parametrize("spec", CATALOG, ids=lambda spec: spec.slug)
def test_reference_solutions_have_no_false_positives(spec):
    result = analyze("debug", spec.reference_solution)
    assert "Likely bugs" not in result
    assert "Syntax" not in result


@pytest.mark.parametrize(
    ("code", "language"),
    [
        ("#include <iostream>\nint main(){std::cout<<1;}", "cpp"),
        ("#include <stdio.h>\nint main(){return 0;}", "c"),
        ("public class Main { public static void main(String[] a){} }", "java"),
        ("const x = 1;\nconsole.log(x);", "javascript"),
        ("print(input())", "python"),
        ("hello there", None),
    ],
)
def test_detect_language(code, language):
    assert detect_language(code) == language


def test_run_reports_python_syntax_error_as_compilation_error():
    result = run_source("python", "def main() -> Nonejj\n    pass\n", "", 10, 128)
    assert result.compile_failed
    assert "SyntaxError: expected ':'" in result.stderr
    assert 'File "main.py", line 1' in result.stderr
    assert "codeforge-exec-" not in result.stderr  # server temp paths never reach users
    assert _failure_status(result.stderr, result.compile_failed).value == "compilation_error"


def test_run_reports_python_exception_as_runtime_error():
    result = run_source("python", "print(1 / 0)\n", "", 10, 128)
    assert not result.compile_failed
    assert "ZeroDivisionError" in result.stderr
    assert _failure_status(result.stderr, result.compile_failed).value == "runtime_error"


@pytest.mark.skipif(not shutil.which("node") or bool(shutil.which("docker")), reason="needs local node")
def test_run_distinguishes_javascript_parse_and_runtime_errors():
    parse = run_source("javascript", "function (\n", "", 10, 128)
    crash = run_source("javascript", "null.x\n", "", 10, 128)
    assert parse.compile_failed and "SyntaxError" in parse.stderr
    assert not crash.compile_failed and "TypeError" in crash.stderr
    assert "node:internal" not in parse.stderr + crash.stderr


@pytest.mark.asyncio
async def test_failed_ai_request_explains_why_and_still_answers():
    from unittest.mock import AsyncMock, patch

    from fastapi import HTTPException

    from app.ai.schemas import AITextRequest
    from app.ai.services.ai_service import AIService

    provider = AsyncMock()
    provider.generate_text.side_effect = HTTPException(
        502, "AI service returned HTTP 401: Incorrect API key provided"
    )
    with patch("app.ai.services.ai_service.get_ai_provider", return_value=provider):
        response = await AIService().debug_code(AITextRequest(content="print(1/0"))
    assert "Incorrect API key provided" in response.result
    assert "Syntax" in response.result  # offline analysis still answered


@pytest.mark.parametrize(
    ("key", "base_url", "model", "expected"),
    [
        ("sk-abc", "https://api.openai.com/v1", "gpt-4o-mini",
         ("https://api.openai.com/v1", "gpt-4o-mini")),
        ("gsk_abc", "https://api.openai.com/v1", "gpt-4o-mini",
         ("https://api.groq.com/openai/v1", "openai/gpt-oss-120b")),
        ("gsk_abc", "https://api.openai.com/v1", "llama-3.1-8b-instant",
         ("https://api.groq.com/openai/v1", "llama-3.1-8b-instant")),
        ("xai-abc", "https://api.openai.com/v1", "gpt-4o-mini",
         ("https://api.x.ai/v1", "grok-3-mini")),
    ],
)
def test_key_prefix_selects_compatible_service(key, base_url, model, expected):
    from app.ai.providers.openai_provider import resolve_endpoint

    assert resolve_endpoint(key, base_url, model) == expected
