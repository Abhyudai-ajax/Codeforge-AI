"""Service layer for Roadmaps, progress calculation, and recommendations."""

from __future__ import annotations

import logging
import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.crud.roadmap import roadmap_crud
from app.models.problem import Problem, ProblemDifficulty
from app.models.roadmap import Roadmap, UserRoadmapSelection
from app.schemas.roadmap import (
    CategoryProgress,
    DifficultyProgress,
    ProblemRecommendation,
    RoadmapResponse,
    RoadmapStageProblemResponse,
    RoadmapStageResponse,
    UserRoadmapProgressOverview,
)

logger = logging.getLogger(__name__)


def _problem_category(problem: Problem) -> str:
    """Derive a category label from the problem's first tag, or fallback to 'General'."""
    if problem.tags:
        return problem.tags[0].name.title()
    return "General"


def _problem_diff_str(problem: Problem) -> str:
    """Return a normalised string value for a problem's difficulty enum."""
    diff_attr = getattr(problem, "difficulty", ProblemDifficulty.EASY)
    return diff_attr.value if hasattr(diff_attr, "value") else str(diff_attr)


class RoadmapService:
    """Business logic for roadmaps, user progression, and recommendations."""

    async def list_roadmaps(self, db: AsyncSession) -> Sequence[Roadmap]:
        return await roadmap_crud.list_roadmaps(db, published_only=True)

    async def get_roadmap(
        self,
        db: AsyncSession,
        identifier: str | uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> RoadmapResponse | None:
        roadmap: Roadmap | None = None
        try:
            roadmap_id = uuid.UUID(str(identifier))
            roadmap = await roadmap_crud.get_by_id(db, roadmap_id)
        except ValueError:
            roadmap = await roadmap_crud.get_by_slug(db, str(identifier))

        if not roadmap:
            return None

        solved_ids: set[uuid.UUID] = set()
        if user_id:
            solved_ids = await roadmap_crud.get_user_solved_problem_ids(db, user_id)

        stage_responses: list[RoadmapStageResponse] = []
        for stage in roadmap.stages:
            prob_responses: list[RoadmapStageProblemResponse] = []
            solved_count = 0
            for sp in stage.problems:
                is_solved = sp.problem_id in solved_ids
                if is_solved:
                    solved_count += 1
                diff_val: str | None = None
                if sp.problem:
                    diff_attr = getattr(sp.problem, "difficulty", None)
                    if diff_attr is not None:
                        diff_val = (
                            diff_attr.value if hasattr(diff_attr, "value") else str(diff_attr)
                        )

                prob_res = RoadmapStageProblemResponse(
                    id=sp.id,
                    stage_id=sp.stage_id,
                    problem_id=sp.problem_id,
                    order=sp.order,
                    is_required=sp.is_required,
                    problem_title=sp.problem.title if sp.problem else None,
                    problem_slug=sp.problem.slug if sp.problem else None,
                    problem_difficulty=diff_val,
                    is_solved=is_solved,
                )
                prob_responses.append(prob_res)

            stage_res = RoadmapStageResponse(
                id=stage.id,
                roadmap_id=stage.roadmap_id,
                title=stage.title,
                slug=stage.slug,
                category_name=stage.category_name,
                description_md=stage.description_md,
                order=stage.order,
                total_problems=len(stage.problems),
                solved_problems=solved_count,
                problems=prob_responses,
            )
            stage_responses.append(stage_res)

        return RoadmapResponse(
            id=roadmap.id,
            slug=roadmap.slug,
            title=roadmap.title,
            description_md=roadmap.description_md,
            is_published=roadmap.is_published,
            is_default=roadmap.is_default,
            order=roadmap.order,
            created_at=roadmap.created_at,
            updated_at=roadmap.updated_at,
            stages=stage_responses,
        )

    async def get_user_active_roadmap(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> RoadmapResponse | None:
        selection = await roadmap_crud.get_user_active_selection(db, user_id)
        if selection:
            return await self.get_roadmap(db, selection.roadmap_id, user_id=user_id)

        default_rm = await roadmap_crud.get_default_roadmap(db)
        if default_rm:
            return await self.get_roadmap(db, default_rm.id, user_id=user_id)

        all_rms = await roadmap_crud.list_roadmaps(db)
        if all_rms:
            return await self.get_roadmap(db, all_rms[0].id, user_id=user_id)

        return None

    async def select_roadmap(
        self, db: AsyncSession, user_id: uuid.UUID, roadmap_id: uuid.UUID
    ) -> UserRoadmapSelection:
        roadmap = await roadmap_crud.get_by_id(db, roadmap_id)
        if not roadmap:
            raise ValueError("Roadmap not found")
        return await roadmap_crud.set_user_selection(db, user_id, roadmap_id)

    async def get_user_progress_overview(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> UserRoadmapProgressOverview:
        active_rm = await self.get_user_active_roadmap(db, user_id)
        solved_ids = await roadmap_crud.get_user_solved_problem_ids(db, user_id)

        stmt_problems = select(Problem).where(Problem.is_active.is_(True))
        res_problems = await db.execute(stmt_problems)
        all_problems = res_problems.scalars().all()

        category_stats: dict[str, dict[str, int]] = {}
        difficulty_stats: dict[str, dict[str, int]] = {
            "easy": {"total": 0, "solved": 0},
            "medium": {"total": 0, "solved": 0},
            "hard": {"total": 0, "solved": 0},
        }

        for p in all_problems:
            cat = _problem_category(p)
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "solved": 0}
            category_stats[cat]["total"] += 1
            if p.id in solved_ids:
                category_stats[cat]["solved"] += 1

            diff_key = _problem_diff_str(p).lower()
            if diff_key not in difficulty_stats:
                difficulty_stats[diff_key] = {"total": 0, "solved": 0}
            difficulty_stats[diff_key]["total"] += 1
            if p.id in solved_ids:
                difficulty_stats[diff_key]["solved"] += 1

        category_progress_list: list[CategoryProgress] = []
        weak_cats: list[tuple[str, float]] = []
        for cat_name, stats in category_stats.items():
            tot = stats["total"]
            sol = stats["solved"]
            pct = (sol / tot * 100.0) if tot > 0 else 0.0
            category_progress_list.append(
                CategoryProgress(
                    category=cat_name,
                    total_problems=tot,
                    solved_problems=sol,
                    completion_percentage=round(pct, 1),
                )
            )
            if tot > 0:
                weak_cats.append((cat_name, pct))

        weak_cats.sort(key=lambda x: x[1])
        weak_category_names = [cat[0] for cat in weak_cats[:3]]

        diff_progress_list: list[DifficultyProgress] = []
        for diff_name, stats in difficulty_stats.items():
            tot = stats["total"]
            sol = stats["solved"]
            pct = (sol / tot * 100.0) if tot > 0 else 0.0
            diff_progress_list.append(
                DifficultyProgress(
                    difficulty=diff_name.capitalize(),
                    total_problems=tot,
                    solved_problems=sol,
                    completion_percentage=round(pct, 1),
                )
            )

        total_rm_problems = 0
        solved_rm_problems = 0
        if active_rm:
            for st in active_rm.stages:
                total_rm_problems += st.total_problems
                solved_rm_problems += st.solved_problems

        overall_pct = (
            (solved_rm_problems / total_rm_problems * 100.0) if total_rm_problems > 0 else 0.0
        )

        return UserRoadmapProgressOverview(
            active_roadmap=active_rm,
            total_roadmap_problems=total_rm_problems,
            solved_roadmap_problems=solved_rm_problems,
            overall_completion_percentage=round(overall_pct, 1),
            categories=category_progress_list,
            difficulties=diff_progress_list,
            weak_categories=weak_category_names,
        )

    async def get_recommendations(
        self, db: AsyncSession, user_id: uuid.UUID, limit: int = 5
    ) -> list[ProblemRecommendation]:
        solved_ids = await roadmap_crud.get_user_solved_problem_ids(db, user_id)
        overview = await self.get_user_progress_overview(db, user_id)

        recommendations: list[ProblemRecommendation] = []
        recommended_prob_ids: set[uuid.UUID] = set()

        # 1. Unsolved problems from active roadmap stages
        if overview.active_roadmap:
            for stage in overview.active_roadmap.stages:
                for sp in stage.problems:
                    if (
                        sp.problem_id not in solved_ids
                        and sp.problem_id not in recommended_prob_ids
                    ):
                        recommendations.append(
                            ProblemRecommendation(
                                problem_id=sp.problem_id,
                                title=sp.problem_title or "Problem",
                                slug=sp.problem_slug or "",
                                category=stage.category_name,
                                difficulty=sp.problem_difficulty or "Easy",
                                reason=(
                                    f"Next problem in your active " f"roadmap stage '{stage.title}'"
                                ),
                            )
                        )
                        recommended_prob_ids.add(sp.problem_id)
                        if len(recommendations) >= limit:
                            return recommendations

        # 2. Unsolved problems in weak categories
        stmt = select(Problem).where(Problem.is_active.is_(True))
        res = await db.execute(stmt)
        all_probs = res.scalars().all()

        for p in all_probs:
            if p.id in solved_ids or p.id in recommended_prob_ids:
                continue

            p_cat = _problem_category(p)
            if p_cat in overview.weak_categories:
                diff_str = _problem_diff_str(p)
                recommendations.append(
                    ProblemRecommendation(
                        problem_id=p.id,
                        title=p.title,
                        slug=p.slug,
                        category=p_cat,
                        difficulty=diff_str,
                        reason=f"Recommended to strengthen weak category '{p_cat}'",
                    )
                )
                recommended_prob_ids.add(p.id)
                if len(recommendations) >= limit:
                    return recommendations

        # 3. Fallback: unsolved problems ordered by difficulty (easy first)
        for p in sorted(
            all_probs, key=lambda x: ["easy", "medium", "hard"].index(_problem_diff_str(x).lower())
        ):
            if p.id in solved_ids or p.id in recommended_prob_ids:
                continue

            p_cat = _problem_category(p)
            diff_str = _problem_diff_str(p)
            recommendations.append(
                ProblemRecommendation(
                    problem_id=p.id,
                    title=p.title,
                    slug=p.slug,
                    category=p_cat,
                    difficulty=diff_str,
                    reason=f"Recommended for {diff_str} difficulty progression",
                )
            )
            recommended_prob_ids.add(p.id)
            if len(recommendations) >= limit:
                return recommendations

        return recommendations


roadmap_service = RoadmapService()
