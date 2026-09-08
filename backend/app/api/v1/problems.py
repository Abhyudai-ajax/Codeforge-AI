"""Problem catalog routes. Routes only orchestrate dependencies and services."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.dependencies import get_ai_service
from app.ai.schemas import AITextResponse
from app.ai.services.ai_service import AIService
from app.core.database import get_db
from app.crud.problem import ProblemRepository
from app.dependencies.auth import get_current_active_user, require_role
from app.models.problem import Problem
from app.models.user import User
from app.schemas.problem import (
    Page,
    ProblemAdminResponse,
    ProblemAIRequest,
    ProblemCreate,
    ProblemListItem,
    ProblemResponse,
    ProblemUpdate,
    RunCodeRequest,
    RunCodeResponse,
    TestCaseResponse,
)
from app.services.problem_ai_service import ProblemAIService
from app.services.problem_execution_service import ProblemExecutionService
from app.services.problem_service import ProblemService

router = APIRouter(prefix="/problems", tags=["DSA Problems"])


def public_problem(problem: Problem) -> ProblemResponse:
    return ProblemResponse(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        tags=[tag.name for tag in problem.tags],
        description_md=problem.description_md,
        input_description=problem.input_description,
        output_description=problem.output_description,
        constraints=problem.constraints,
        examples=problem.examples,
        starter_code=problem.starter_code,
        supported_languages=problem.supported_languages,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        is_active=problem.is_active,
        created_at=problem.created_at,
        updated_at=problem.updated_at,
    )


@router.get("/search", response_model=Page)
@router.get("", response_model=Page)
async def list_problems(
    difficulty: str | None = None,
    language: str | None = None,
    tags: str | None = None,
    search: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> Page:
    problems, total = await ProblemRepository(db).list(
        difficulty=difficulty,
        language=language,
        tag=tags,
        search=search,
        offset=offset,
        limit=limit,
    )
    return Page(
        items=[
            ProblemListItem(
                id=p.id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                tags=[t.name for t in p.tags],
            )
            for p in problems
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.post("", response_model=ProblemAdminResponse, status_code=status.HTTP_201_CREATED)
async def create_problem(
    payload: ProblemCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> ProblemAdminResponse:
    problem = await ProblemService(db).create(payload)
    return ProblemAdminResponse(
        **public_problem(problem).model_dump(),
        editorial_md=problem.editorial_md,
        test_cases=[TestCaseResponse.model_validate(c) for c in problem.test_cases],
    )


@router.get("/{problem_id}", response_model=ProblemResponse)
async def get_problem(problem_id: UUID, db: AsyncSession = Depends(get_db)) -> ProblemResponse:
    problem = await ProblemRepository(db).get(problem_id)
    if not problem or not problem.is_active:
        raise HTTPException(404, "Problem not found.")
    return public_problem(problem)


@router.post("/{problem_id}/run", response_model=RunCodeResponse)
async def run_problem_code(
    problem_id: UUID,
    payload: RunCodeRequest,
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> RunCodeResponse:
    return await ProblemExecutionService(db).run(problem_id, payload)


@router.post(
    "/{problem_id}/ai/hint",
    response_model=AITextResponse,
    summary="Get an AI hint grounded in this problem",
    description=(
        "Returns a strategy hint built from the stored statement and constraints. Include the "
        "editor's current source to get advice about the attempt in progress."
    ),
)
async def problem_ai_hint(
    problem_id: UUID,
    payload: ProblemAIRequest,
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ProblemAIService(db, ai_service).hint(problem_id, payload)


@router.post(
    "/{problem_id}/ai/explain",
    response_model=AITextResponse,
    summary="Explain an approach in the context of this problem",
)
async def problem_ai_explain(
    problem_id: UUID,
    payload: ProblemAIRequest,
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ProblemAIService(db, ai_service).explain(problem_id, payload)


@router.post(
    "/{problem_id}/ai/review",
    response_model=AITextResponse,
    summary="Review a solution against this problem's constraints",
)
async def problem_ai_review(
    problem_id: UUID,
    payload: ProblemAIRequest,
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service),
) -> AITextResponse:
    return await ProblemAIService(db, ai_service).review(problem_id, payload)


@router.patch("/{problem_id}", response_model=ProblemAdminResponse)
async def update_problem(
    problem_id: UUID,
    payload: ProblemUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> ProblemAdminResponse:
    problem = await ProblemService(db).update(problem_id, payload)
    return ProblemAdminResponse(
        **public_problem(problem).model_dump(),
        editorial_md=problem.editorial_md,
        test_cases=[TestCaseResponse.model_validate(c) for c in problem.test_cases],
    )


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_problem(
    problem_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin"))
) -> Response:
    await ProblemService(db).delete(problem_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{problem_id}/test-cases", response_model=list[TestCaseResponse])
async def test_cases(
    problem_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(require_role("admin"))
) -> list[TestCaseResponse]:
    problem = await ProblemRepository(db).get(problem_id, include_cases=True)
    if not problem:
        raise HTTPException(404, "Problem not found.")
    return [TestCaseResponse.model_validate(case) for case in problem.test_cases]
