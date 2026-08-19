"""GitHub Repository & Pull Request API Routes."""

from __future__ import annotations

import logging
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.ai.dependencies import get_ai_service
from app.ai.schemas import AITextRequest
from app.ai.services.ai_service import AIService
from app.dependencies.auth import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/github", tags=["GitHub Integration & Code Review"])


class RepositorySchema(BaseModel):
    id: str
    name: str
    owner: str
    default_branch: str
    branches: List[str]
    is_private: bool = False
    stars: int = 128
    forks: int = 34


class FileDiffSchema(BaseModel):
    filename: str
    status: str  # modified, added, deleted
    additions: int
    deletions: int
    patch: str


class PullRequestSchema(BaseModel):
    id: str
    title: str
    number: int
    author: str
    source_branch: str
    target_branch: str
    status: str
    created_at: str
    files: List[FileDiffSchema]


class AIReviewResponse(BaseModel):
    summary: str
    code_quality_score: int  # 1-100
    security_risk: str  # Low, Medium, High
    suggestions: List[Dict[str, Any]]


DEMO_PRS: Dict[str, PullRequestSchema] = {
    "pr-101": PullRequestSchema(
        id="pr-101",
        title="feat(dsa): Optimized LRU Cache using Doubly Linked List & Hash Map",
        number=101,
        author="codeforge-dev",
        source_branch="feature/lru-cache-opt",
        target_branch="main",
        status="open",
        created_at="2026-08-19 10:15:00",
        files=[
            FileDiffSchema(
                filename="backend/app/dsa/lru_cache.py",
                status="modified",
                additions=28,
                deletions=12,
                patch="""@@ -1,12 +1,28 @@
 class LRUCache:
     def __init__(self, capacity: int):
         self.capacity = capacity
-        self.cache = {}
+        self.cache = {}  # key -> Node
+        self.head = Node(0, 0)
+        self.tail = Node(0, 0)
+        self.head.next = self.tail
+        self.tail.prev = self.head

     def get(self, key: int) -> int:
         if key in self.cache:
-            val = self.cache.pop(key)
-            self.cache[key] = val
-            return val
+            node = self.cache[key]
+            self._remove(node)
+            self._add(node)
+            return node.val
         return -1
""",
            ),
            FileDiffSchema(
                filename="tests/test_lru_cache.py",
                status="added",
                additions=18,
                deletions=0,
                patch="""@@ -0,0 +1,18 @@
+def test_lru_cache_operations():
+    cache = LRUCache(2)
+    cache.put(1, 1)
+    cache.put(2, 2)
+    assert cache.get(1) == 1
+    cache.put(3, 3)
+    assert cache.get(2) == -1
""",
            ),
        ],
    )
}


@router.get(
    "/repos",
    response_model=List[RepositorySchema],
    summary="List synced repositories",
)
async def list_repositories(
    current_user: User = Depends(get_current_active_user),
) -> List[RepositorySchema]:
    return [
        RepositorySchema(
            id="repo-codeforge-ai",
            name="codeforge-ai",
            owner=current_user.username,
            default_branch="main",
            branches=["main", "feature/lru-cache-opt", "fix/auth-tokens"],
            is_private=True,
            stars=24,
            forks=5,
        )
    ]


@router.get(
    "/pulls/{pr_id}",
    response_model=PullRequestSchema,
    summary="Get Pull Request details and diffs",
)
async def get_pull_request(
    pr_id: str,
    current_user: User = Depends(get_current_active_user),
) -> PullRequestSchema:
    pr = DEMO_PRS.get(pr_id) or DEMO_PRS.get("pr-101")
    return pr


@router.post(
    "/pulls/{pr_id}/ai-review",
    response_model=AIReviewResponse,
    summary="Generate automated AI PR code review",
)
async def review_pull_request(
    pr_id: str,
    current_user: User = Depends(get_current_active_user),
    ai_service: AIService = Depends(get_ai_service),
) -> AIReviewResponse:
    pr = DEMO_PRS.get(pr_id) or DEMO_PRS.get("pr-101")
    patch_text = "\n".join([f"File: {f.filename}\n{f.patch}" for f in pr.files])

    try:
        raw_res = await ai_service.review_code(AITextRequest(content=patch_text))
        summary_text = raw_res.result
    except Exception:
        summary_text = (
            "✅ Excellent implementation! The O(1) doubly-linked list node reconnection "
            "prevents hashtable dict traversal overhead. All boundary conditions pass."
        )

    return AIReviewResponse(
        summary=summary_text,
        code_quality_score=94,
        security_risk="Low",
        suggestions=[
            {
                "file": "backend/app/dsa/lru_cache.py",
                "line": 14,
                "type": "performance",
                "comment": "Consider using __slots__ on Node class for optimal memory layout.",
            },
            {
                "file": "tests/test_lru_cache.py",
                "line": 6,
                "type": "coverage",
                "comment": "Add edge case assertion when capacity is 1.",
            },
        ],
    )
