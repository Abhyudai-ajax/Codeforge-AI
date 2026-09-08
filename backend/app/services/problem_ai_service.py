"""AI assistance scoped to a specific DSA problem.

The generic ``/ai/*`` routes take arbitrary text. These helpers build the prompt
from the stored problem statement so a hint is grounded in the actual task and
the constraints the judge enforces, rather than whatever the client pasted.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import AITextRequest, AITextResponse
from app.ai.services.ai_service import AIService
from app.core import languages
from app.crud.problem import ProblemRepository
from app.models.problem import Problem
from app.schemas.problem import ProblemAIRequest

_MAX_CONTENT = 30_000
_MAX_CONTEXT = 8_000


class ProblemAIService:
    def __init__(self, session: AsyncSession, ai_service: AIService) -> None:
        self.session = session
        self.ai = ai_service

    async def _problem(self, problem_id: UUID) -> Problem:
        problem = await ProblemRepository(self.session).get(problem_id)
        if not problem or not problem.is_active:
            raise HTTPException(404, "Problem not found.")
        return problem

    @staticmethod
    def _context(problem: Problem, payload: ProblemAIRequest) -> str:
        parts = [
            f"Problem: {problem.title} ({problem.difficulty.value})",
            f"Tags: {', '.join(tag.name for tag in problem.tags) or 'none'}",
            f"Time limit: {problem.time_limit_ms} ms; memory limit: {problem.memory_limit_mb} MB.",
            "",
            "Statement:",
            problem.description_md,
        ]
        if problem.constraints:
            parts += ["", "Constraints:", *(f"- {rule}" for rule in problem.constraints)]
        if payload.source_code.strip():
            parts += ["", f"The candidate is writing {languages.normalize(payload.language)}."]
        return "\n".join(parts)[:_MAX_CONTEXT]

    def _request(self, problem: Problem, payload: ProblemAIRequest) -> AITextRequest:
        # `content` is what the model reasons over; fall back to the statement
        # itself when the editor is still empty so a hint is always possible.
        content = payload.source_code.strip() or problem.description_md
        return AITextRequest(
            content=content[:_MAX_CONTENT],
            additional_context=self._context(problem, payload),
        )

    async def hint(self, problem_id: UUID, payload: ProblemAIRequest) -> AITextResponse:
        problem = await self._problem(problem_id)
        return await self.ai.generate_dsa_hint(self._request(problem, payload))

    async def explain(self, problem_id: UUID, payload: ProblemAIRequest) -> AITextResponse:
        problem = await self._problem(problem_id)
        return await self.ai.explain_code(self._request(problem, payload))

    async def review(self, problem_id: UUID, payload: ProblemAIRequest) -> AITextResponse:
        problem = await self._problem(problem_id)
        if not payload.source_code.strip():
            raise HTTPException(422, "Source code is required for a review.")
        return await self.ai.review_code(self._request(problem, payload))
