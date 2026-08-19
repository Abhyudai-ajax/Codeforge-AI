"""Pydantic schemas for Problems and Submissions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TestCaseSchema(BaseModel):
    """Single testcase schema."""

    input: Any
    expected_output: Any
    is_sample: bool = True


class ProblemBase(BaseModel):
    """Base problem schema."""

    title: str
    slug: str
    difficulty: str
    category: str
    description_md: str
    starter_code: Dict[str, str]
    test_cases: List[TestCaseSchema]
    constraints: List[str]
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    acceptance_rate: float = 65.0


class ProblemCreate(ProblemBase):
    """Problem creation schema."""

    pass


class ProblemResponse(ProblemBase):
    """Problem response schema."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProblemListItem(BaseModel):
    """Simplified problem representation for list view."""

    id: UUID
    title: str
    slug: str
    difficulty: str
    category: str
    acceptance_rate: float

    model_config = ConfigDict(from_attributes=True)


class CodeRunRequest(BaseModel):
    """Request schema for running code against testcases."""

    code: str
    language: str = "python"
    custom_test_cases: Optional[List[Dict[str, Any]]] = None


class TestCaseResult(BaseModel):
    """Result of a single testcase evaluation."""

    test_case: int
    input: Any
    expected_output: Any
    actual_output: str
    passed: bool
    runtime_ms: float
    error_message: Optional[str] = None


class CodeRunResponse(BaseModel):
    """Response from code run or submission execution."""

    status: str
    passed_test_cases: int
    total_test_cases: int
    runtime_ms: float
    memory_mb: float
    test_results: List[TestCaseResult]


class SubmissionCreate(BaseModel):
    """Request schema to submit a problem solution."""

    code: str
    language: str = "python"


class SubmissionResponse(BaseModel):
    """Response schema for a solution submission."""

    id: UUID
    user_id: UUID
    problem_id: UUID
    language: str
    code: str
    status: str
    passed_test_cases: int
    total_test_cases: int
    runtime_ms: float
    memory_mb: float
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
