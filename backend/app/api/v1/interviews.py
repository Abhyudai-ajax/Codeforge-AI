"""API router for Mock Interview System."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.interview import (
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    InterviewCodeSubmissionRequest,
    InterviewFeedbackResponse,
    InterviewSessionResponse,
    StartInterviewRequest,
)
from app.services.interview_service import interview_service

router = APIRouter(prefix="/interviews", tags=["Interviews"])


@router.post(
    "/sessions",
    response_model=InterviewSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_interview_session(
    payload: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionResponse:
    """Start a new mock interview session."""
    return await interview_service.start_session(
        db,
        user_id=current_user.id,
        type=payload.type,
        title=payload.title,
        time_limit_minutes=payload.time_limit_minutes,
    )


@router.get("/sessions/me", response_model=list[InterviewSessionResponse])
async def list_my_interview_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InterviewSessionResponse]:
    """List mock interview sessions for authenticated user."""
    sessions = await interview_service.list_user_sessions(
        db, user_id=current_user.id, limit=limit, offset=offset
    )
    results: list[InterviewSessionResponse] = []
    for s in sessions:
        detail = await interview_service.get_session(db, session_id=s.id, user_id=current_user.id)
        results.append(detail)
    return results


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionResponse:
    """Get details of a specific interview session."""
    try:
        return await interview_service.get_session(
            db, session_id=session_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/sessions/{session_id}/answer",
    response_model=InterviewAnswerResponse,
)
async def submit_interview_answer(
    session_id: uuid.UUID,
    payload: InterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewAnswerResponse:
    """Submit text answer for an interview question."""
    try:
        return await interview_service.submit_answer(
            db,
            user_id=current_user.id,
            session_id=session_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/{session_id}/submit-code",
    response_model=InterviewAnswerResponse,
)
async def submit_interview_code(
    session_id: uuid.UUID,
    payload: InterviewCodeSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewAnswerResponse:
    """Link a DSA submission to an interview coding question."""
    try:
        return await interview_service.submit_code(
            db,
            user_id=current_user.id,
            session_id=session_id,
            question_id=payload.question_id,
            submission_id=payload.submission_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/sessions/{session_id}/finish",
    response_model=InterviewSessionResponse,
)
async def finish_interview_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewSessionResponse:
    """Finish interview session and generate evaluation feedback."""
    try:
        return await interview_service.finish_session(
            db, user_id=current_user.id, session_id=session_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/sessions/{session_id}/feedback",
    response_model=InterviewFeedbackResponse,
)
async def get_interview_feedback(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InterviewFeedbackResponse:
    """Get evaluation report/feedback for a finished session."""
    session = await interview_service.get_session(
        db, session_id=session_id, user_id=current_user.id
    )
    if not session.feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation feedback not generated yet for this session",
        )
    return session.feedback
