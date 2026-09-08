"""Integrity tests for the shipped DSA catalog.

The important one is ``test_reference_solution_matches_every_case``: it runs each
problem's reference solution against its own test data, so a typo in an expected
output fails here instead of failing a user's correct submission in production.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from app.core import languages
from app.db.problem_catalog import CATALOG, CATALOG_BY_SLUG, ProblemSpec

EXPECTED_PROBLEM_COUNT = 50


def _normalize(text: str) -> str:
    """Whitespace normalization identical to the judge's comparison."""
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def test_catalog_ships_fifty_problems():
    assert len(CATALOG) == EXPECTED_PROBLEM_COUNT


def test_slugs_are_unique():
    slugs = [problem.slug for problem in CATALOG]
    assert len(set(slugs)) == len(slugs)
    assert len(CATALOG_BY_SLUG) == len(slugs)


def test_every_difficulty_and_a_broad_topic_spread():
    difficulties = {problem.difficulty for problem in CATALOG}
    assert difficulties == {"easy", "medium", "hard"}
    assert len({problem.category for problem in CATALOG}) >= 15


@pytest.mark.parametrize("problem", CATALOG, ids=lambda problem: problem.slug)
def test_problem_metadata_is_complete(problem: ProblemSpec):
    assert problem.slug == problem.slug.lower()
    assert problem.title and problem.summary
    assert problem.input_description and problem.output_description
    assert problem.constraints
    assert problem.editorial
    assert len(problem.cases) >= 4
    assert problem.sample_count <= len(problem.cases)
    assert problem.difficulty in {"easy", "medium", "hard"}


@pytest.mark.parametrize("problem", CATALOG, ids=lambda problem: problem.slug)
def test_starter_code_covers_every_supported_language(problem: ProblemSpec):
    starter = problem.starter_code
    assert set(starter) == set(languages.LANGUAGE_IDS)
    assert {"c", "cpp"} <= set(starter), "C and C++ must be offered on every problem"
    for language_id, code in starter.items():
        assert code.strip(), f"{problem.slug} has empty {language_id} starter code"
        assert "{header}" not in code, f"{problem.slug} left an unrendered placeholder"
    # Java's entry point must be named Main to match the runner's javac/java invocation.
    assert "class Main" in starter["java"]


@pytest.mark.parametrize("problem", CATALOG, ids=lambda problem: problem.slug)
def test_description_embeds_the_sample_cases(problem: ProblemSpec):
    description = problem.description_md
    assert "## Input" in description and "## Output" in description
    for stdin_data, _ in problem.cases[: problem.sample_count]:
        assert stdin_data.strip() in description


@pytest.mark.parametrize("problem", CATALOG, ids=lambda problem: problem.slug)
def test_reference_solution_matches_every_case(problem: ProblemSpec):
    """Prove the seeded expected outputs are actually correct."""
    for index, (stdin_data, expected) in enumerate(problem.cases):
        completed = subprocess.run(
            [sys.executable, "-c", problem.reference_solution],
            input=stdin_data,
            text=True,
            capture_output=True,
            timeout=60,
        )
        assert (
            completed.returncode == 0
        ), f"{problem.slug} case {index} crashed:\n{completed.stderr}"
        assert _normalize(completed.stdout) == _normalize(expected), (
            f"{problem.slug} case {index} produced {completed.stdout!r}, " f"expected {expected!r}"
        )
