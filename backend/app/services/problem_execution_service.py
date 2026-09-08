"""Synchronous execution for the editor's run-code workflow."""

from __future__ import annotations

import asyncio
import time
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import languages
from app.crud.problem import ProblemRepository
from app.models.problem import SubmissionStatus
from app.schemas.problem import (
    RunCodeRequest,
    RunCodeResponse,
    RunTestCase,
    RunTestResult,
)
from app.workers.sandbox import run_source
from app.workers.submission import _failure_status, _same_output


class ProblemExecutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run(self, problem_id: UUID, payload: RunCodeRequest) -> RunCodeResponse:
        problem = await ProblemRepository(self.session).get(problem_id, include_cases=True)
        if not problem or not problem.is_active:
            raise HTTPException(404, "Problem not found.")

        language = languages.normalize(payload.language)
        if language not in problem.supported_languages:
            raise HTTPException(422, "Language is not supported by this problem.")
        if not languages.is_supported(language):
            raise HTTPException(422, "Language is not available for execution.")

        cases = payload.custom_test_cases
        if cases is None:
            cases = [
                RunTestCase(
                    input_data=case.input_data,
                    expected_output=case.expected_output,
                )
                for case in problem.test_cases
                if case.is_public
            ]
        if not cases:
            raise HTTPException(422, "This problem has no runnable test cases.")

        results: list[RunTestResult] = []
        total_runtime = 0
        for index, case in enumerate(cases, start=1):
            started = time.monotonic()
            result = await asyncio.to_thread(
                run_source,
                language,
                payload.source_code,
                case.input_data,
                problem.time_limit_ms / 1000,
                problem.memory_limit_mb,
            )
            runtime_ms = int((time.monotonic() - started) * 1000)
            total_runtime += runtime_ms
            passed = (
                not result.timed_out
                and result.exit_code == 0
                and _same_output(result.stdout, case.expected_output)
            )
            error = ""
            if result.timed_out:
                error = "Time limit exceeded."
            elif result.exit_code != 0:
                error = "Program failed in the isolated runner."
            results.append(
                RunTestResult(
                    test_case=index,
                    input_data=case.input_data,
                    expected_output=case.expected_output,
                    actual_output=result.stdout,
                    passed=passed,
                    runtime_ms=runtime_ms,
                    error=error,
                )
            )
            if not passed:
                break

        passed_count = sum(result.passed for result in results)
        status = SubmissionStatus.ACCEPTED.value
        if passed_count != len(cases):
            failed = results[-1]
            if failed.error == "Time limit exceeded.":
                status = SubmissionStatus.TIME_LIMIT_EXCEEDED.value
            elif failed.error:
                status = _failure_status(language, failed.error).value
            else:
                status = SubmissionStatus.WRONG_ANSWER.value
        return RunCodeResponse(
            status=status,
            passed_test_cases=passed_count,
            total_test_cases=len(cases),
            runtime_ms=total_runtime,
            test_results=results,
        )
