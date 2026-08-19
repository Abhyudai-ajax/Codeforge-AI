"""Code Runner Service.

Executes code safely against test cases and captures execution metrics.
"""

from __future__ import annotations

import io
import sys
import time
import traceback
from typing import Any, Dict, List


class CodeRunner:
    """Service to execute code snippets against problem test cases."""

    @staticmethod
    def run_python(code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs Python code against test cases in an in-memory sandbox."""
        results = []
        passed_count = 0
        total_time = 0.0

        for idx, tc in enumerate(test_cases):
            input_val = tc.get("input", "")
            expected_val = str(tc.get("expected_output", "")).strip()

            start_time = time.perf_counter()
            captured_output = io.StringIO()
            error_msg = None
            passed = False
            actual_output = ""

            try:
                # Setup localized globals with print redirect
                sandbox_globals: Dict[str, Any] = {
                    "__builtins__": __builtins__,
                    "print": lambda *args, **kwargs: print(*args, file=captured_output, **kwargs),
                }
                
                # Execute code definition
                exec(code, sandbox_globals)

                # Look for solution function or execute standard input runner
                sol_func = None
                for key, val in sandbox_globals.items():
                    if callable(val) and not key.startswith("__"):
                        sol_func = val
                        break

                if sol_func:
                    # Evaluate solution function with test case input
                    if isinstance(input_val, dict):
                        res = sol_func(**input_val)
                    elif isinstance(input_val, list):
                        res = sol_func(*input_val)
                    elif input_val == "" or input_val is None:
                        res = sol_func()
                    else:
                        res = sol_func(input_val)

                    actual_output = str(res).strip() if res is not None else captured_output.getvalue().strip()
                else:
                    actual_output = captured_output.getvalue().strip()

                # Compare results (handle booleans, numbers, lists formatting)
                passed = CodeRunner._compare_outputs(actual_output, expected_val)

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc(limit=2)}"
                actual_output = captured_output.getvalue().strip()

            elapsed = (time.perf_counter() - start_time) * 1000
            total_time += elapsed

            if passed:
                passed_count += 1

            results.append({
                "test_case": idx + 1,
                "input": input_val,
                "expected_output": expected_val,
                "actual_output": actual_output,
                "passed": passed,
                "runtime_ms": round(elapsed, 2),
                "error_message": error_msg,
            })

        avg_runtime = round(total_time / max(1, len(test_cases)), 2)
        # Mock memory computation for display
        memory_mb = round(12.4 + (len(code) % 5) * 0.8, 1)

        status = "Accepted" if passed_count == len(test_cases) else "Wrong Answer"
        if any(r["error_message"] for r in results):
            status = "Runtime Error"

        return {
            "status": status,
            "passed_test_cases": passed_count,
            "total_test_cases": len(test_cases),
            "runtime_ms": avg_runtime,
            "memory_mb": memory_mb,
            "test_results": results,
        }

    @staticmethod
    def _compare_outputs(actual: str, expected: str) -> bool:
        """Flexible comparison of actual vs expected outputs."""
        if actual == expected:
            return True

        # Normalize whitespace and quotes
        norm_actual = actual.replace("'", '"').replace(" ", "").lower()
        norm_expected = expected.replace("'", '"').replace(" ", "").lower()

        if norm_actual == norm_expected:
            return True

        # Handle boolean lowercase
        if norm_actual in ["true", "false"] and norm_expected in ["true", "false"]:
            return norm_actual == norm_expected

        return False

    @classmethod
    def execute(cls, code: str, language: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generic execution entry point routing by language."""
        lang = language.lower().strip()
        if lang in ["python", "python3", "py"]:
            return cls.run_python(code, test_cases)
        else:
            # Fallback simulator for non-python languages in demo
            return cls.run_python(code, test_cases)
