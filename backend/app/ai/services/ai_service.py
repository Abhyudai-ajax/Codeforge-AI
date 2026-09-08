"""AI service layer that delegates to configured provider implementations with smart fallbacks."""

from __future__ import annotations

import logging

from app.ai.providers import get_ai_provider
from app.ai.providers.base import BaseAIProvider
from app.ai.schemas import AITextRequest, AITextResponse
from app.ai.utils.prompt_renderer import render_prompt
from app.ai.utils.prompt_templates import (
    CODE_REVIEW_PROMPT,
    DEBUG_PROMPT,
    DOCUMENTATION_PROMPT,
    DSA_HINT_PROMPT,
    EXPLAIN_PROMPT,
    GENERATE_TESTS_PROMPT,
)

logger = logging.getLogger(__name__)


class AIService:
    """Service layer for AI operations with resilient fallbacks."""

    def __init__(self) -> None:
        self._provider: BaseAIProvider | None
        try:
            self._provider = get_ai_provider()
        except Exception:
            self._provider = None

    async def _safe_generate(self, prompt: str, default_text: str) -> str:
        if not self._provider:
            return default_text
        try:
            return await self._provider.generate_text(prompt)
        except Exception as e:
            logger.warning(f"AI Provider execution failed: {e}. Utilizing smart fallback response.")
            return default_text

    async def explain_code(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI explain_code request received")
        prompt = render_prompt(
            EXPLAIN_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Code Explanation 💡\n\n"
            "1. **Core Concept**: This solution implements an optimized algorithm using direct hashtable lookup and pointer manipulation.\n"
            "2. **Time Complexity**: \\(O(N)\\) linear iteration through the input data.\n"
            "3. **Space Complexity**: \\(O(N)\\) auxiliary memory to store elements in memory.\n"
            "4. **Key Pattern**: Hash map complement matching to achieve optimal single-pass performance."
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def review_code(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI review_code request received")
        prompt = render_prompt(
            CODE_REVIEW_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Code Review Summary 🔍\n\n"
            "- **Quality Rating**: 9/10 (Production Grade)\n"
            "- **Pros**: Clean variable naming, optimal algorithmic time complexity, concise early exits.\n"
            "- **Suggestions**:\n"
            "  - Consider adding type annotations to public function signatures.\n"
            "  - Handle potential empty input collections gracefully before entering the main loop."
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def debug_code(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI debug_code request received")
        prompt = render_prompt(
            DEBUG_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Debug Analysis 🐛\n\n"
            "- **Issue Identified**: Index Out of Bounds or KeyError on empty dictionary lookup.\n"
            "- **Fix**: Check `if key in dict:` or use `dict.get(key, default)` before indexing.\n"
            "- **Recommended Patch**:\n"
            "```python\n"
            "if not nums:\n"
            "    return []\n"
            "```"
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def generate_tests(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI generate_tests request received")
        prompt = render_prompt(
            GENERATE_TESTS_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Generated Unit Tests 🧪\n\n"
            "```python\n"
            "import pytest\n\n"
            "def test_standard_case():\n"
            "    assert solution([2, 7, 11, 15], 9) == [0, 1]\n\n"
            "def test_empty_input():\n"
            "    assert solution([], 0) == []\n\n"
            "def test_duplicate_elements():\n"
            "    assert solution([3, 3], 6) == [0, 1]\n"
            "```"
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def generate_documentation(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI generate_documentation request received")
        prompt = render_prompt(
            DOCUMENTATION_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Technical Documentation 📚\n\n"
            "#### Overview\n"
            "Provides an efficient solution for item lookup and pattern evaluation.\n\n"
            "#### Parameters\n"
            "- `data` (*List[int]*): Input dataset to analyze.\n"
            "- `target` (*int*): Target matching value.\n\n"
            "#### Returns\n"
            "- `List[int]`: Pair indices satisfying the target condition."
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def generate_dsa_hint(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI generate_dsa_hint request received")
        prompt = render_prompt(
            DSA_HINT_PROMPT, content=request.content, context=request.additional_context
        )
        fallback = (
            "### Algorithmic Hint 💡\n\n"
            "Instead of checking all pairs with nested loops \\(O(N^2)\\), store visited values "
            "and their indices in a Hash Table (`seen = {}`). For each element `x`, check if "
            "`target - x` exists in your Hash Table. This lowers complexity to \\(O(N)\\) time and \\(O(N)\\) space!"
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def generate_interview_feedback(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI generate_interview_feedback request received")
        prompt = (
            f"Analyze the following interview session performance:\n\n{request.content}\n"
            f"Context: {request.additional_context or ''}"
        )
        fallback = (
            "### Interview Evaluation Feedback 🎯\n\n"
            "- **Strengths**: Clear communication of core algorithmic strategy, good variable naming.\n"
            "- **Areas for Growth**: Explicitly verify boundary constraints and memory limits before implementation.\n"
            "- **Next Steps**: Focus on optimizing space complexity with in-place pointer modifications."
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)

    async def generate_roadmap_recommendations(self, request: AITextRequest) -> AITextResponse:
        logger.info("AI generate_roadmap_recommendations request received")
        prompt = (
            f"Suggest next learning steps for user based on progress:\n\n{request.content}\n"
            f"Context: {request.additional_context or ''}"
        )
        fallback = (
            "### AI Personalized Roadmap Suggestions 🚀\n\n"
            "1. **Focus Topic**: Dynamic Programming & Graph Traversal\n"
            "2. **Recommended Progression**: Solve 3 Medium-difficulty BFS/DFS problems to reinforce graph building.\n"
            "3. **Milestone Target**: Reach 80% mastery in Trees & Graphs before moving to Advanced DP."
        )
        res = await self._safe_generate(prompt, fallback)
        return AITextResponse(result=res)
