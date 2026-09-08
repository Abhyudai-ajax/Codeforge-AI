"""Request and response contracts for the asynchronous DSA platform."""

from datetime import datetime
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.problem import ProblemDifficulty, SubmissionStatus


class TestCaseCreate(BaseModel):
    input_data: str = Field(max_length=100_000)
    expected_output: str = Field(max_length=100_000)
    is_public: bool = False
    order: int = Field(default=0, ge=0)


class TestCaseResponse(BaseModel):
    id: UUID
    input_data: str
    expected_output: str
    is_public: bool
    order: int
    model_config = ConfigDict(from_attributes=True)


class ProblemCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9-]+$", max_length=100)
    title: str = Field(min_length=1, max_length=200)
    difficulty: ProblemDifficulty
    description_md: str = Field(min_length=1)
    input_description: str = ""
    output_description: str = ""
    constraints: list[str] = Field(default_factory=list)
    examples: list[dict] = Field(default_factory=list)
    starter_code: dict[str, str] = Field(default_factory=dict)
    supported_languages: list[str] = Field(default_factory=lambda: ["python"])
    editorial_md: str | None = None
    time_limit_ms: int = Field(default=2000, ge=1, le=60_000)
    memory_limit_mb: int = Field(default=256, ge=16, le=1024)
    is_active: bool = True
    test_cases: list[TestCaseCreate] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    difficulty: ProblemDifficulty | None = None
    description_md: str | None = None
    input_description: str | None = None
    output_description: str | None = None
    constraints: list[str] | None = None
    examples: list[dict] | None = None
    starter_code: dict[str, str] | None = None
    supported_languages: list[str] | None = None
    editorial_md: str | None = None
    time_limit_ms: int | None = Field(default=None, ge=1, le=60_000)
    memory_limit_mb: int | None = Field(default=None, ge=16, le=1024)
    is_active: bool | None = None
    test_cases: list[TestCaseCreate] | None = None
    tags: list[str] | None = None


class ProblemListItem(BaseModel):
    id: UUID
    slug: str
    title: str
    difficulty: ProblemDifficulty
    tags: list[str]


class ProblemResponse(ProblemListItem):
    description_md: str
    input_description: str
    output_description: str
    constraints: list[str]
    examples: list[dict]
    starter_code: dict[str, str]
    supported_languages: list[str]
    time_limit_ms: int
    memory_limit_mb: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProblemAdminResponse(ProblemResponse):
    editorial_md: str | None
    test_cases: list[TestCaseResponse]


class Page(BaseModel):
    items: list[ProblemListItem]
    total: int
    offset: int
    limit: int


class SubmissionCreate(BaseModel):
    problem_id: UUID
    source_code: str = Field(min_length=1, max_length=200_000)
    language: str = Field(min_length=1, max_length=30)
    room_id: UUID | None = None


class ProblemSubmitRequest(BaseModel):
    source_code: str = Field(
        validation_alias=AliasChoices("source_code", "code"),
        min_length=1,
        max_length=200_000,
    )
    language: str = Field(min_length=1, max_length=30)


class RunTestCase(BaseModel):
    input_data: str = Field(
        validation_alias=AliasChoices("input_data", "input"),
        max_length=100_000,
    )
    expected_output: str = Field(max_length=100_000)


class RunCodeRequest(BaseModel):
    source_code: str = Field(
        validation_alias=AliasChoices("source_code", "code"),
        min_length=1,
        max_length=200_000,
    )
    language: str = Field(min_length=1, max_length=30)
    custom_test_cases: list[RunTestCase] | None = Field(default=None, max_length=100)


class ProblemAIRequest(BaseModel):
    """Ask for AI help on a problem, optionally including the editor's contents."""

    source_code: str = Field(
        default="",
        validation_alias=AliasChoices("source_code", "code"),
        max_length=30_000,
    )
    language: str = Field(default="python", min_length=1, max_length=30)


class RunTestResult(BaseModel):
    test_case: int
    input_data: str
    expected_output: str
    actual_output: str
    passed: bool
    runtime_ms: int
    error: str = ""


class RunCodeResponse(BaseModel):
    status: str
    passed_test_cases: int
    total_test_cases: int
    runtime_ms: int
    test_results: list[RunTestResult]


class SubmissionResponse(BaseModel):
    id: UUID
    user_id: UUID
    problem_id: UUID
    room_id: UUID | None
    language: str
    status: SubmissionStatus
    runtime_ms: int | None
    memory_kb: int | None
    passed_test_count: int
    total_test_count: int
    score: int
    output: str
    error_output: str
    created_at: datetime
    completed_at: datetime | None
    model_config = ConfigDict(from_attributes=True)
