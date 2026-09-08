"""CRUD operations for Mock Interview System."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import (
    InterviewAnswer,
    InterviewFeedback,
    InterviewQuestion,
    InterviewSession,
    InterviewStatus,
    InterviewType,
)


class CRUDInterview:
    """CRUD data layer for interview sessions and evaluation reports."""

    async def create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: InterviewType = InterviewType.DSA,
        title: str = "Mock Interview Session",
        time_limit_minutes: int = 45,
    ) -> InterviewSession:
        session = InterviewSession(
            user_id=user_id,
            type=type,
            title=title,
            time_limit_minutes=time_limit_minutes,
            status=InterviewStatus.CREATED,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session_by_id(
        self, db: AsyncSession, session_id: uuid.UUID
    ) -> InterviewSession | None:
        stmt = select(InterviewSession).where(InterviewSession.id == session_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_sessions(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[InterviewSession]:
        stmt = (
            select(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return res.scalars().all()

    async def add_question(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        question_text: str,
        problem_id: uuid.UUID | None = None,
        question_type: str = "coding",
        order: int = 0,
        points: int = 100,
    ) -> InterviewQuestion:
        q = InterviewQuestion(
            session_id=session_id,
            problem_id=problem_id,
            question_text=question_text,
            question_type=question_type,
            order=order,
            points=points,
        )
        db.add(q)
        await db.commit()
        await db.refresh(q)
        return q

    async def record_answer(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        answer_text: str = "",
        submission_id: uuid.UUID | None = None,
        score: float = 0.0,
        feedback_text: str = "",
    ) -> InterviewAnswer:
        ans = InterviewAnswer(
            question_id=question_id,
            session_id=session_id,
            user_id=user_id,
            answer_text=answer_text,
            submission_id=submission_id,
            score=score,
            feedback_text=feedback_text,
        )
        db.add(ans)
        await db.commit()
        await db.refresh(ans)
        return ans

    async def save_feedback(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        overall_score: float,
        strengths: list[str],
        improvements: list[str],
        summary_md: str,
    ) -> InterviewFeedback:
        stmt = select(InterviewFeedback).where(InterviewFeedback.session_id == session_id)
        res = await db.execute(stmt)
        existing = res.scalar_one_or_none()

        if existing:
            existing.overall_score = overall_score
            existing.strengths = strengths
            existing.improvements = improvements
            existing.summary_md = summary_md
            existing.evaluated_at = datetime.utcnow()
            fb = existing
        else:
            fb = InterviewFeedback(
                session_id=session_id,
                overall_score=overall_score,
                strengths=strengths,
                improvements=improvements,
                summary_md=summary_md,
            )
            db.add(fb)

        await db.commit()
        await db.refresh(fb)
        return fb

    async def update_status(
        self,
        db: AsyncSession,
        session: InterviewSession,
        status: InterviewStatus,
        score: float | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> InterviewSession:
        session.status = status
        if score is not None:
            session.score = score
        if start_time is not None:
            session.start_time = start_time
        if end_time is not None:
            session.end_time = end_time
        await db.commit()
        await db.refresh(session)
        return session


interview_crud = CRUDInterview()
