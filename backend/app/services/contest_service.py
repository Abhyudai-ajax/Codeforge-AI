"""Business rules for contests, registrations, submissions, scoring, and leaderboards."""

from __future__ import annotations

from datetime import UTC, datetime
from math import floor
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.contest import ContestRepository
from app.models.contest import (
    Contest,
    ContestParticipant,
    ContestProblem,
    ContestSubmission,
)
from app.models.problem import Submission, SubmissionStatus
from app.models.user import User
from app.schemas.contest import (
    ContestCreate,
    ContestLeaderboardEntry,
    ContestLeaderboardPage,
    ContestListItem,
    ContestProblemResponse,
    ContestSubmissionCreate,
    ContestUpdate,
    UserContestHistoryItem,
)
from app.schemas.problem import ProblemResponse, SubmissionCreate, SubmissionResponse
from app.services.problem_service import SubmissionService


class ContestService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContestRepository(session)

    @staticmethod
    def get_status(contest: Contest, now: datetime | None = None) -> str:
        if now is None:
            now = datetime.now(UTC)
        # Ensure timezone-aware comparison
        start = contest.start_time
        end = contest.end_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)

        if now < start:
            return "upcoming"
        if start <= now <= end:
            return "running"
        return "ended"

    async def create(self, payload: ContestCreate, current_user: User) -> Contest:
        if await self.repo.by_slug(payload.slug):
            raise HTTPException(409, "Contest slug already exists.")
        if payload.end_time <= payload.start_time:
            raise HTTPException(422, "End time must be after start time.")

        contest = Contest(
            title=payload.title,
            slug=payload.slug,
            description_md=payload.description_md,
            start_time=payload.start_time,
            end_time=payload.end_time,
            is_published=payload.is_published,
            created_by_id=current_user.id,
        )
        self.session.add(contest)
        await self.session.commit()
        await self.session.refresh(contest)

        for prob_in in payload.problems:
            cp = ContestProblem(
                contest_id=contest.id,
                problem_id=prob_in.problem_id,
                order=prob_in.order,
                points=prob_in.points,
                label=prob_in.label,
            )
            self.session.add(cp)

        await self.session.commit()
        await self.session.refresh(contest)
        return contest

    async def update(self, contest_id: UUID, payload: ContestUpdate) -> Contest:
        contest = await self.repo.get(contest_id, include_problems=True)
        if not contest:
            raise HTTPException(404, "Contest not found.")

        values = payload.model_dump(exclude_unset=True, exclude={"problems"})
        for key, val in values.items():
            setattr(contest, key, val)

        if contest.end_time <= contest.start_time:
            raise HTTPException(422, "End time must be after start time.")

        if payload.problems is not None:
            # Re-associate contest problems
            stmt = select(ContestProblem).where(ContestProblem.contest_id == contest.id)
            existing_cps = (await self.session.execute(stmt)).scalars().all()
            for cp in existing_cps:
                await self.session.delete(cp)

            for prob_in in payload.problems:
                cp = ContestProblem(
                    contest_id=contest.id,
                    problem_id=prob_in.problem_id,
                    order=prob_in.order,
                    points=prob_in.points,
                    label=prob_in.label,
                )
                self.session.add(cp)

        await self.session.commit()
        await self.session.refresh(contest)
        return contest

    async def delete(self, contest_id: UUID) -> None:
        contest = await self.repo.get(contest_id)
        if not contest:
            raise HTTPException(404, "Contest not found.")
        await self.session.delete(contest)
        await self.session.commit()

    async def list_contests(
        self,
        status_filter: str | None,
        current_user: User | None,
        offset: int,
        limit: int,
    ) -> tuple[list[ContestListItem], int]:
        is_admin = bool(
            current_user and getattr(current_user.role, "value", current_user.role) == "admin"
        )
        contests, total = await self.repo.list_contests(
            status_filter=status_filter,
            include_unpublished=is_admin,
            offset=offset,
            limit=limit,
        )
        now = datetime.now(UTC)
        result_items = []
        for c in contests:
            status_str = self.get_status(c, now)
            participant_count = await self.repo.count_participants(c.id)
            is_reg = False
            if current_user:
                reg = await self.repo.get_registration(c.id, current_user.id)
                is_reg = reg is not None

            item = ContestListItem(
                id=c.id,
                title=c.title,
                slug=c.slug,
                start_time=c.start_time,
                end_time=c.end_time,
                is_published=c.is_published,
                status=status_str,
                participant_count=participant_count,
                is_registered=is_reg,
                created_at=c.created_at,
            )
            result_items.append(item)
        return result_items, total

    async def get_contest_detail(self, contest_id: UUID, current_user: User | None) -> dict:
        contest = await self.repo.get(contest_id, include_problems=True)
        if not contest:
            raise HTTPException(404, "Contest not found.")

        is_admin = (
            current_user and getattr(current_user.role, "value", current_user.role) == "admin"
        )
        if not contest.is_published and not is_admin:
            raise HTTPException(404, "Contest not found.")

        now = datetime.now(UTC)
        status_str = self.get_status(contest, now)
        participant_count = await self.repo.count_participants(contest.id)
        is_reg = False
        if current_user:
            reg = await self.repo.get_registration(contest.id, current_user.id)
            is_reg = reg is not None

        # Build problem list
        # Gating rule: Problem details (description/test cases) are hidden before start_time for non-admins
        problems_res = []
        can_view_problems = is_admin or status_str in {"running", "ended"}
        for cp in contest.problems:
            prob_resp = None
            if can_view_problems and cp.problem:
                prob_resp = ProblemResponse(
                    id=cp.problem.id,
                    slug=cp.problem.slug,
                    title=cp.problem.title,
                    difficulty=cp.problem.difficulty,
                    tags=[t.name for t in cp.problem.tags],
                    description_md=cp.problem.description_md,
                    input_description=cp.problem.input_description,
                    output_description=cp.problem.output_description,
                    constraints=cp.problem.constraints,
                    examples=cp.problem.examples,
                    starter_code=cp.problem.starter_code,
                    supported_languages=cp.problem.supported_languages,
                    time_limit_ms=cp.problem.time_limit_ms,
                    memory_limit_mb=cp.problem.memory_limit_mb,
                    is_active=cp.problem.is_active,
                    created_at=cp.problem.created_at,
                    updated_at=cp.problem.updated_at,
                )

            problems_res.append(
                ContestProblemResponse(
                    id=cp.id,
                    contest_id=cp.contest_id,
                    problem_id=cp.problem_id,
                    order=cp.order,
                    points=cp.points,
                    label=cp.label,
                    problem=prob_resp,
                )
            )

        return {
            "id": contest.id,
            "title": contest.title,
            "slug": contest.slug,
            "description_md": contest.description_md,
            "start_time": contest.start_time,
            "end_time": contest.end_time,
            "is_published": contest.is_published,
            "status": status_str,
            "participant_count": participant_count,
            "is_registered": is_reg,
            "created_at": contest.created_at,
            "problems": problems_res,
        }

    async def register(self, contest_id: UUID, current_user: User) -> dict:
        contest = await self.repo.get(contest_id)
        if not contest or not contest.is_published:
            raise HTTPException(404, "Contest not found.")

        now = datetime.now(UTC)
        status_str = self.get_status(contest, now)
        if status_str == "ended":
            raise HTTPException(400, "Cannot register for an ended contest.")

        reg = await self.repo.register_user(contest.id, current_user.id)
        return {
            "contest_id": str(contest.id),
            "user_id": str(current_user.id),
            "registered_at": reg.registered_at,
            "message": "Successfully registered for contest.",
        }

    async def unregister(self, contest_id: UUID, current_user: User) -> dict:
        contest = await self.repo.get(contest_id)
        if not contest:
            raise HTTPException(404, "Contest not found.")

        now = datetime.now(UTC)
        status_str = self.get_status(contest, now)
        if status_str != "upcoming":
            raise HTTPException(400, "Can only unregister before the contest starts.")

        success = await self.repo.unregister_user(contest.id, current_user.id)
        if not success:
            raise HTTPException(400, "User is not registered for this contest.")
        return {"message": "Successfully unregistered from contest."}

    async def submit_contest_solution(
        self,
        contest_id: UUID,
        payload: ContestSubmissionCreate,
        current_user: User,
    ) -> SubmissionResponse:
        contest = await self.repo.get(contest_id, include_problems=True)
        if not contest or not contest.is_published:
            raise HTTPException(404, "Contest not found.")

        now = datetime.now(UTC)
        status_str = self.get_status(contest, now)
        is_admin = getattr(current_user.role, "value", current_user.role) == "admin"
        if status_str != "running" and not is_admin:
            raise HTTPException(
                400, "Contest submissions are only allowed while the contest is running."
            )

        reg = await self.repo.get_registration(contest.id, current_user.id)
        if not reg and not is_admin:
            raise HTTPException(403, "You must register for the contest before submitting.")

        # Ensure problem is part of contest
        cp = next((p for p in contest.problems if p.problem_id == payload.problem_id), None)
        if not cp:
            raise HTTPException(400, "Problem is not part of this contest.")

        # Create underlying submission
        sub_payload = SubmissionCreate(
            problem_id=payload.problem_id,
            language=payload.language,
            source_code=payload.source_code,
        )
        submission = await SubmissionService(self.session).create(current_user, sub_payload)

        # Record contest submission linkage
        await self.repo.record_contest_submission(
            contest_id=contest.id,
            problem_id=payload.problem_id,
            submission_id=submission.id,
            user_id=current_user.id,
        )
        return submission

    async def process_submission_score(
        self, contest_id: UUID, user_id: UUID, problem_id: UUID, submission: Submission
    ) -> None:
        """Invoked when a contest submission result is recorded, to update participant score & time penalty."""
        contest = await self.repo.get(contest_id, include_problems=True)
        if not contest:
            return

        cp = next((p for p in contest.problems if p.problem_id == problem_id), None)
        if not cp:
            return

        participant = await self.repo.get_participant(contest.id, user_id)
        if not participant:
            participant = ContestParticipant(contest_id=contest.id, user_id=user_id)
            self.session.add(participant)
            await self.session.commit()

        if submission.status == SubmissionStatus.ACCEPTED:
            # Check if user already solved this problem in this contest
            solved_stmt = (
                select(ContestSubmission)
                .join(Submission)
                .where(
                    ContestSubmission.contest_id == contest.id,
                    ContestSubmission.problem_id == problem_id,
                    ContestSubmission.user_id == user_id,
                    Submission.status == SubmissionStatus.ACCEPTED,
                    Submission.id != submission.id,
                )
            )
            already_solved = (await self.session.execute(solved_stmt)).scalar_one_or_none()
            if not already_solved:
                # First AC for this problem
                # Count prior wrong submissions for this problem in this contest
                wrong_stmt = (
                    select(func.count())
                    .select_from(ContestSubmission)
                    .join(Submission)
                    .where(
                        ContestSubmission.contest_id == contest.id,
                        ContestSubmission.problem_id == problem_id,
                        ContestSubmission.user_id == user_id,
                        Submission.status != SubmissionStatus.ACCEPTED,
                    )
                )
                wrong_count = (await self.session.execute(wrong_stmt)).scalar_one()

                # Calculate minutes from contest start
                start = contest.start_time
                if start.tzinfo is None:
                    start = start.replace(tzinfo=UTC)
                sub_time = submission.created_at
                if sub_time.tzinfo is None:
                    sub_time = sub_time.replace(tzinfo=UTC)

                minutes_elapsed = max(0, floor((sub_time - start).total_seconds() / 60))
                penalty_minutes = minutes_elapsed + (wrong_count * 20)

                participant.total_score += cp.points
                participant.total_penalty += penalty_minutes
                participant.problems_solved += 1
                await self.session.commit()

    async def get_leaderboard(
        self, contest_id: UUID, offset: int = 0, limit: int = 50
    ) -> ContestLeaderboardPage:
        contest = await self.repo.get(contest_id)
        if not contest:
            raise HTTPException(404, "Contest not found.")

        rows, total = await self.repo.get_leaderboard(contest_id, offset=offset, limit=limit)
        entries = []
        for index, (participant, user) in enumerate(rows):
            rank = offset + index + 1
            entries.append(
                ContestLeaderboardEntry(
                    rank=rank,
                    user_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                    total_score=participant.total_score,
                    total_penalty=participant.total_penalty,
                    problems_solved=participant.problems_solved,
                )
            )

        return ContestLeaderboardPage(items=entries, total=total, offset=offset, limit=limit)

    async def get_user_contest_history(self, current_user: User) -> list[UserContestHistoryItem]:
        history_rows = await self.repo.get_user_contests(current_user.id)
        items = []
        for row in history_rows:
            contest = row["contest"]
            items.append(
                UserContestHistoryItem(
                    contest_id=contest.id,
                    title=contest.title,
                    slug=contest.slug,
                    start_time=contest.start_time,
                    end_time=contest.end_time,
                    registered_at=row["registered_at"],
                    rank=row["rank"],
                    total_score=row["total_score"],
                    total_penalty=row["total_penalty"],
                    problems_solved=row["problems_solved"],
                )
            )
        return items
