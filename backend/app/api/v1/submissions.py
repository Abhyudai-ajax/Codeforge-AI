"""Authenticated asynchronous submission and progress endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.problem import Problem, Submission, UserProblemProgress
from app.models.user import User
from app.schemas.problem import (
    ProblemSubmitRequest,
    SubmissionCreate,
    SubmissionResponse,
)
from app.services.problem_service import SubmissionService

router = APIRouter(tags=["Submissions & Progress"])


@router.post(
    "/submissions", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED
)
async def create_submission(
    payload: SubmissionCreate,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    return await SubmissionService(db).create(user, payload)


@router.post(
    "/problems/{problem_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_problem_solution(
    problem_id: UUID,
    payload: ProblemSubmitRequest,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    return await SubmissionService(db).create(
        user,
        SubmissionCreate(
            problem_id=problem_id,
            source_code=payload.source_code,
            language=payload.language,
        ),
    )


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
@router.get("/submissions/{submission_id}/result", response_model=SubmissionResponse)
async def get_submission(
    submission_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SubmissionResponse:
    return await SubmissionService(db).get_for_user(submission_id, user)


@router.get("/problems/{problem_id}/submissions", response_model=list[SubmissionResponse])
async def problem_submissions(
    problem_id: UUID,
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[SubmissionResponse]:
    return list(
        (
            await db.execute(
                select(Submission)
                .where(Submission.problem_id == problem_id, Submission.user_id == user.id)
                .order_by(Submission.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars()
    )


@router.get("/users/me/submissions", response_model=list[SubmissionResponse])
async def my_submissions(
    user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[SubmissionResponse]:
    return list(
        (
            await db.execute(
                select(Submission)
                .where(Submission.user_id == user.id)
                .order_by(Submission.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        ).scalars()
    )


@router.get("/users/me/progress/problems")
async def progress_problems(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    rows = (
        await db.execute(
            select(UserProblemProgress, Problem)
            .join(Problem, Problem.id == UserProblemProgress.problem_id)
            .where(UserProblemProgress.user_id == user.id)
        )
    ).all()
    return [
        {
            "problem_id": str(problem.id),
            "slug": problem.slug,
            "attempts": progress.attempts,
            "accepted_submissions": progress.accepted_submissions,
            "failed_submissions": progress.failed_submissions,
            "first_solved_at": progress.first_solved_at,
        }
        for progress, problem in rows
    ]


@router.get("/users/me/progress")
@router.get("/users/me/stats")
async def progress_summary(
    user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)
) -> dict:
    rows = (
        await db.execute(
            select(UserProblemProgress, Problem.difficulty)
            .join(Problem, Problem.id == UserProblemProgress.problem_id)
            .where(UserProblemProgress.user_id == user.id)
        )
    ).all()
    solved = [row for row in rows if row[0].first_solved_at]
    by_difficulty = {
        difficulty: sum(1 for progress, value in solved if value.value == difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    return {
        "attempted": len(rows),
        "solved": len(solved),
        "by_difficulty": by_difficulty,
        "total_attempts": sum(row[0].attempts for row in rows),
    }
