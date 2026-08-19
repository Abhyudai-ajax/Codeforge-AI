"""LeetCode-style DSA Problems API Routes."""

from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.problem import Problem, Submission
from app.models.user import User
from app.schemas.problem import (
    CodeRunRequest,
    CodeRunResponse,
    ProblemListItem,
    ProblemResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from app.services.code_runner import CodeRunner

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/problems", tags=["Problems & DSA Engine"])


@router.get(
    "",
    response_model=List[ProblemListItem],
    summary="List all DSA problems",
    description="Retrieve a paginated list of DSA problems with difficulty, category, and search filters.",
)
async def list_problems(
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Easy, Medium, Hard)"),
    category: Optional[str] = Query(None, description="Filter by category (Arrays, Dynamic Programming, etc.)"),
    search: Optional[str] = Query(None, description="Search by title or slug"),
    db: AsyncSession = Depends(get_db),
) -> List[ProblemListItem]:
    stmt = select(Problem)

    if difficulty:
        stmt = stmt.where(Problem.difficulty.ilike(difficulty))
    if category:
        stmt = stmt.where(Problem.category.ilike(category))
    if search:
        stmt = stmt.where(Problem.title.ilike(f"%{search}%") | Problem.slug.ilike(f"%{search}%"))

    stmt = stmt.order_by(Problem.created_at.asc())
    result = await db.execute(stmt)
    problems = result.scalars().all()
    return problems


@router.get(
    "/{problem_identifier}",
    response_model=ProblemResponse,
    summary="Get problem details",
    description="Retrieve problem statement, starter code, testcases, and constraints by UUID or slug.",
)
async def get_problem(
    problem_identifier: str,
    db: AsyncSession = Depends(get_db),
) -> ProblemResponse:
    try:
        problem_uuid = UUID(problem_identifier)
        stmt = select(Problem).where(Problem.id == problem_uuid)
    except ValueError:
        stmt = select(Problem).where(Problem.slug == problem_identifier)

    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    return problem


@router.post(
    "/{problem_id}/run",
    response_model=CodeRunResponse,
    summary="Run code against sample test cases",
    description="Executes code against sample or custom test cases and returns execution metrics.",
)
async def run_code(
    problem_id: UUID,
    payload: CodeRunRequest,
    db: AsyncSession = Depends(get_db),
) -> CodeRunResponse:
    stmt = select(Problem).where(Problem.id == problem_id)
    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    test_cases = payload.custom_test_cases or problem.test_cases
    exec_result = CodeRunner.execute(payload.code, payload.language, test_cases)
    return CodeRunResponse(**exec_result)


@router.post(
    "/{problem_id}/submit",
    response_model=SubmissionResponse,
    summary="Submit solution",
    description="Evaluates user solution against all problem testcases and records submission.",
)
async def submit_solution(
    problem_id: UUID,
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    stmt = select(Problem).where(Problem.id == problem_id)
    result = await db.execute(stmt)
    problem = result.scalar_one_or_none()

    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

    exec_result = CodeRunner.execute(payload.code, payload.language, problem.test_cases)

    # Save submission
    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        language=payload.language,
        code=payload.code,
        status=exec_result["status"],
        passed_test_cases=exec_result["passed_test_cases"],
        total_test_cases=exec_result["total_test_cases"],
        runtime_ms=exec_result["runtime_ms"],
        memory_mb=exec_result["memory_mb"],
        error_message="\n".join([r["error_message"] for r in exec_result["test_results"] if r["error_message"]]) or None,
    )

    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return submission


@router.get(
    "/{problem_id}/submissions",
    response_model=List[SubmissionResponse],
    summary="Get problem submission history",
    description="Retrieve past submissions for the logged in user on this problem.",
)
async def get_submissions(
    problem_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[SubmissionResponse]:
    stmt = (
        select(Submission)
        .where(Submission.problem_id == problem_id, Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
