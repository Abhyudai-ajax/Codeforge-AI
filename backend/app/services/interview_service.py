"""Service layer for Mock Interview System."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.interview import interview_crud
from app.models.interview import (
    InterviewSession,
    InterviewStatus,
    InterviewType,
)
from app.models.notification import NotificationType
from app.models.problem import Problem, Submission, SubmissionStatus
from app.schemas.interview import (
    InterviewAnswerResponse,
    InterviewFeedbackResponse,
    InterviewQuestionResponse,
    InterviewSessionResponse,
)
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)


class InterviewService:
    """Business logic for interview sessions and feedback generation."""

    async def start_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        type: InterviewType = InterviewType.DSA,
        title: str = "Mock Interview Session",
        time_limit_minutes: int = 45,
    ) -> InterviewSessionResponse:
        session = await interview_crud.create_session(
            db,
            user_id=user_id,
            type=type,
            title=title,
            time_limit_minutes=time_limit_minutes,
        )

        if type == InterviewType.DSA:
            stmt = (
                select(Problem)
                .where(Problem.is_active.is_(True))
                .order_by(Problem.created_at.asc())
                .limit(2)
            )
            res = await db.execute(stmt)
            probs = res.scalars().all()
            for idx, p in enumerate(probs):
                await interview_crud.add_question(
                    db,
                    session_id=session.id,
                    question_text=f"Solve '{p.title}': {p.description_md[:200]}...",
                    problem_id=p.id,
                    question_type="coding",
                    order=idx,
                    points=100,
                )
        elif type == InterviewType.SYSTEM_DESIGN:
            questions_data = [
                (
                    "Design a URL Shortening Service (like TinyURL) capable "
                    "of handling 100M daily active users.",
                    "system_design",
                    0,
                    100,
                ),
                (
                    "Explain how you would handle rate limiting and load "
                    "balancing across microservices.",
                    "system_design",
                    1,
                    100,
                ),
            ]
            for text, qtype, order, pts in questions_data:
                await interview_crud.add_question(
                    db,
                    session_id=session.id,
                    question_text=text,
                    question_type=qtype,
                    order=order,
                    points=pts,
                )
        else:  # Behavioral
            questions_data = [
                (
                    "Describe a situation where you had to resolve a conflict "
                    "within your engineering team.",
                    "behavioral",
                    0,
                    100,
                ),
                (
                    "How do you prioritize technical debt versus feature velocity?",
                    "behavioral",
                    1,
                    100,
                ),
            ]
            for text, qtype, order, pts in questions_data:
                await interview_crud.add_question(
                    db,
                    session_id=session.id,
                    question_text=text,
                    question_type=qtype,
                    order=order,
                    points=pts,
                )

        updated_session = await interview_crud.update_status(
            db,
            session=session,
            status=InterviewStatus.IN_PROGRESS,
            start_time=datetime.now(UTC),
        )

        return await self.get_session(db, session_id=updated_session.id, user_id=user_id)  # type: ignore

    async def get_session(
        self, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> InterviewSessionResponse:
        session = await interview_crud.get_session_by_id(db, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Interview session not found or unauthorized")

        q_responses: list[InterviewQuestionResponse] = []
        for q in session.questions:
            q_responses.append(
                InterviewQuestionResponse(
                    id=q.id,
                    session_id=q.session_id,
                    problem_id=q.problem_id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    order=q.order,
                    points=q.points,
                    problem_title=q.problem.title if q.problem else None,
                )
            )

        a_responses: list[InterviewAnswerResponse] = []
        for a in session.answers:
            a_responses.append(
                InterviewAnswerResponse(
                    id=a.id,
                    question_id=a.question_id,
                    session_id=a.session_id,
                    user_id=a.user_id,
                    answer_text=a.answer_text,
                    submission_id=a.submission_id,
                    score=a.score,
                    feedback_text=a.feedback_text,
                    submitted_at=a.submitted_at,
                )
            )

        fb_res: InterviewFeedbackResponse | None = None
        if session.feedback:
            fb = session.feedback
            fb_res = InterviewFeedbackResponse(
                id=fb.id,
                session_id=fb.session_id,
                overall_score=fb.overall_score,
                strengths=fb.strengths,
                improvements=fb.improvements,
                summary_md=fb.summary_md,
                evaluated_at=fb.evaluated_at,
            )

        return InterviewSessionResponse(
            id=session.id,
            user_id=session.user_id,
            type=session.type,
            title=session.title,
            status=session.status,
            score=session.score,
            time_limit_minutes=session.time_limit_minutes,
            start_time=session.start_time,
            end_time=session.end_time,
            created_at=session.created_at,
            questions=q_responses,
            answers=a_responses,
            feedback=fb_res,
        )

    async def list_user_sessions(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> Sequence[InterviewSession]:
        return await interview_crud.list_user_sessions(
            db, user_id=user_id, limit=limit, offset=offset
        )

    async def submit_answer(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        answer_text: str,
    ) -> InterviewAnswerResponse:
        session = await interview_crud.get_session_by_id(db, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or unauthorized")

        question = next((q for q in session.questions if q.id == question_id), None)
        if not question:
            raise ValueError("Question not found in session")

        words = len(answer_text.strip().split())
        chars = len(answer_text.strip())
        # Smarter heuristic: decent answers usually have 20+ words and some length.
        if words > 50:
            score = 100.0
        elif words > 20:
            score = 80.0
        elif words > 5:
            score = 50.0
        else:
            score = min(100.0, float(chars * 0.5))

        ans = await interview_crud.record_answer(
            db,
            question_id=question_id,
            session_id=session_id,
            user_id=user_id,
            answer_text=answer_text,
            score=score,
            feedback_text="Answer logged successfully.",
        )

        return InterviewAnswerResponse(
            id=ans.id,
            question_id=ans.question_id,
            session_id=ans.session_id,
            user_id=ans.user_id,
            answer_text=ans.answer_text,
            submission_id=ans.submission_id,
            score=ans.score,
            feedback_text=ans.feedback_text,
            submitted_at=ans.submitted_at,
        )

    async def submit_code(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        submission_id: uuid.UUID,
    ) -> InterviewAnswerResponse:
        session = await interview_crud.get_session_by_id(db, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or unauthorized")

        stmt = select(Submission).where(
            Submission.id == submission_id, Submission.user_id == user_id
        )
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            raise ValueError("Submission not found")

        score = 100.0 if sub.status == SubmissionStatus.ACCEPTED else 30.0
        fb_msg = (
            "Accepted solution!"
            if sub.status == SubmissionStatus.ACCEPTED
            else f"Submission status: {sub.status.value}"
        )

        ans = await interview_crud.record_answer(
            db,
            question_id=question_id,
            session_id=session_id,
            user_id=user_id,
            answer_text=sub.source_code,
            submission_id=sub.id,
            score=score,
            feedback_text=fb_msg,
        )

        return InterviewAnswerResponse(
            id=ans.id,
            question_id=ans.question_id,
            session_id=ans.session_id,
            user_id=ans.user_id,
            answer_text=ans.answer_text,
            submission_id=ans.submission_id,
            score=ans.score,
            feedback_text=ans.feedback_text,
            submitted_at=ans.submitted_at,
        )

    async def finish_session(
        self, db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> InterviewSessionResponse:
        session = await interview_crud.get_session_by_id(db, session_id)
        if not session or session.user_id != user_id:
            raise ValueError("Session not found or unauthorized")

        total_score = 0.0
        if session.answers:
            scores = [a.score for a in session.answers]
            total_score = round(sum(scores) / len(scores), 1)
        else:
            total_score = 0.0

        strengths = [
            "Demonstrated clear understanding of algorithmic constraints.",
            "Structured response cleanly with proper edge-case handling.",
        ]
        improvements = [
            "Practice optimizing memory complexity in hashtable lookups.",
            "Explain time-complexity trade-offs explicitly during discussion.",
        ]
        summary_md = (
            f"### Mock Interview Evaluation Report 🎯\n\n"
            f"- **Overall Score**: {total_score} / 100\n"
            f"- **Session Status**: Completed\n"
            f"- **Duration**: {session.time_limit_minutes} minutes\n\n"
            f"Great performance! Your solution demonstrated good problem solving."
        )

        await interview_crud.save_feedback(
            db,
            session_id=session_id,
            overall_score=total_score,
            strengths=strengths,
            improvements=improvements,
            summary_md=summary_md,
        )

        await interview_crud.update_status(
            db,
            session=session,
            status=InterviewStatus.COMPLETED,
            score=total_score,
            end_time=datetime.now(UTC),
        )

        await notification_service.notify_user(
            db,
            user_id=user_id,
            type=NotificationType.INTERVIEW_COMPLETED,
            title="Interview Session Completed",
            message=(
                f"Your mock interview '{session.title}' is finished. "
                f"Overall score: {total_score}/100"
            ),
            data={"session_id": str(session.id), "score": total_score},
        )

        return await self.get_session(db, session_id=session_id, user_id=user_id)


interview_service = InterviewService()
