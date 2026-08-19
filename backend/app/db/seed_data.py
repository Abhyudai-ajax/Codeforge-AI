"""Seed script to populate database with curated DSA Problems, Demo Projects, and Users."""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.models.problem import Problem, ProblemDifficulty
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

SEED_PROBLEMS = [
    {
        "slug": "two-sum",
        "title": "1. Two Sum",
        "difficulty": ProblemDifficulty.EASY.value,
        "category": "Arrays",
        "acceptance_rate": 52.4,
        "description_md": """Given an array of integers `nums` and an integer `target`, return *indices of the two numbers such that they add up to `target`*.

You may assume that each input would have ***exactly one solution***, and you may not use the same element twice.

You can return the answer in any order.

### Example 1:
```text
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

### Example 2:
```text
Input: nums = [3,2,4], target = 6
Output: [1,2]
```

### Constraints:
- `2 <= nums.length <= 10^4`
- `-10^9 <= nums[i] <= 10^9`
- `-10^9 <= target <= 10^9`
- **Only one valid answer exists.**
""",
        "starter_code": {
            "python": "def twoSum(nums: list[int], target: int) -> list[int]:\n    # Write your solution here\n    pass\n",
            "javascript": "function twoSum(nums, target) {\n    // Write your solution here\n};\n",
        },
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected_output": "[0, 1]", "is_sample": True},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected_output": "[1, 2]", "is_sample": True},
            {"input": {"nums": [3, 3], "target": 6}, "expected_output": "[0, 1]", "is_sample": False},
        ],
        "constraints": [
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "Only one valid answer exists.",
        ],
    },
    {
        "slug": "valid-anagram",
        "title": "242. Valid Anagram",
        "difficulty": ProblemDifficulty.EASY.value,
        "category": "Strings",
        "acceptance_rate": 64.1,
        "description_md": """Given two strings `s` and `t`, return `true` *if `t` is an anagram of `s`, and `false` otherwise*.

An Anagram is a word or phrase formed by rearranging the letters of a different word or phrase, typically using all the original letters exactly once.

### Example 1:
```text
Input: s = "anagram", t = "nagaram"
Output: true
```

### Example 2:
```text
Input: s = "rat", t = "car"
Output: false
```
""",
        "starter_code": {
            "python": "def isAnagram(s: str, t: str) -> bool:\n    # Write your solution here\n    pass\n",
            "javascript": "function isAnagram(s, t) {\n    // Write your solution here\n};\n",
        },
        "test_cases": [
            {"input": {"s": "anagram", "t": "nagaram"}, "expected_output": "True", "is_sample": True},
            {"input": {"s": "rat", "t": "car"}, "expected_output": "False", "is_sample": True},
        ],
        "constraints": [
            "1 <= s.length, t.length <= 5 * 10^4",
            "s and t consist of lowercase English letters.",
        ],
    },
    {
        "slug": "reverse-linked-list",
        "title": "206. Reverse Linked List",
        "difficulty": ProblemDifficulty.EASY.value,
        "category": "Linked List",
        "acceptance_rate": 76.2,
        "description_md": """Given the `head` of a singly linked list, reverse the list, and return *the reversed list*.

### Example 1:
```text
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]
```
""",
        "starter_code": {
            "python": "def reverseList(head):\n    prev = None\n    curr = head\n    while curr:\n        nxt = curr.next\n        curr.next = prev\n        prev = curr\n        curr = nxt\n    return prev\n",
        },
        "test_cases": [
            {"input": {"head": [1, 2, 3, 4, 5]}, "expected_output": "[5, 4, 3, 2, 1]", "is_sample": True},
        ],
        "constraints": ["The number of nodes in the list is in the range [0, 5000]."],
    },
    {
        "slug": "lru-cache",
        "title": "146. LRU Cache",
        "difficulty": ProblemDifficulty.MEDIUM.value,
        "category": "Design",
        "acceptance_rate": 42.8,
        "description_md": """Design a data structure that follows the constraints of a **Least Recently Used (LRU) Cache**.

Implement the `LRUCache` class:
- `LRUCache(int capacity)` Initialize the LRU cache with positive size `capacity`.
- `int get(int key)` Return the value of the `key` if the key exists, otherwise return `-1`.
- `void put(int key, int value)` Update the value of the key if it exists. Otherwise, add the key-value pair to the cache. If capacity is exceeded, **evict** the least recently used key.

The functions `get` and `put` must each run in \\(O(1)\\) average time complexity.
""",
        "starter_code": {
            "python": "class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n\n    def get(self, key: int) -> int:\n        pass\n\n    def put(self, key: int, value: int) -> None:\n        pass\n",
        },
        "test_cases": [
            {"input": {"actions": ["LRUCache", "put", "put", "get", "put", "get"], "params": [[2], [1, 1], [2, 2], [1], [3, 3], [2]]}, "expected_output": "[null, null, null, 1, null, -1]", "is_sample": True},
        ],
        "constraints": ["1 <= capacity <= 3000", "At most 2 * 10^5 calls will be made to get and put."],
    },
    {
        "slug": "3sum",
        "title": "15. 3Sum",
        "difficulty": ProblemDifficulty.MEDIUM.value,
        "category": "Arrays",
        "acceptance_rate": 34.7,
        "description_md": """Given an integer array nums, return all the triplets `[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and `j != k`, and `nums[i] + nums[j] + nums[k] == 0`.

Notice that the solution set must not contain duplicate triplets.
""",
        "starter_code": {
            "python": "def threeSum(nums: list[int]) -> list[list[int]]:\n    # Write solution here\n    pass\n",
        },
        "test_cases": [
            {"input": {"nums": [-1, 0, 1, 2, -1, -4]}, "expected_output": "[[-1, -1, 2], [-1, 0, 1]]", "is_sample": True},
        ],
        "constraints": ["3 <= nums.length <= 3000"],
    },
]


async def seed_all():
    logger.info("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. Seed Demo User
        stmt = select(User).where(User.username == "demo_dev")
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            logger.info("Creating demo user 'demo_dev'...")
            from app.core.security import hash_password
            hashed_pwd = hash_password("password123")
            user = User(
                id=uuid4(),
                username="demo_dev",
                email="demo@codeforge.ai",
                hashed_password=hashed_pwd,
                full_name="Alex Rivera",
                role=UserRole.USER,
                bio="FAANG Senior Software Engineer | Algorithmic Problem Solver",
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # 2. Seed Problems
        for prob_data in SEED_PROBLEMS:
            stmt = select(Problem).where(Problem.slug == prob_data["slug"])
            res = await db.execute(stmt)
            existing_prob = res.scalar_one_or_none()

            if not existing_prob:
                logger.info(f"Seeding problem '{prob_data['title']}'...")
                prob = Problem(
                    id=uuid4(),
                    slug=prob_data["slug"],
                    title=prob_data["title"],
                    difficulty=prob_data["difficulty"],
                    category=prob_data["category"],
                    acceptance_rate=prob_data["acceptance_rate"],
                    description_md=prob_data["description_md"],
                    starter_code=prob_data["starter_code"],
                    test_cases=prob_data["test_cases"],
                    constraints=prob_data["constraints"],
                )
                db.add(prob)

        # 3. Seed Demo VSCode Project & Files
        stmt = select(Project).where(Project.title == "CodeForge AI Playground")
        res = await db.execute(stmt)
        project = res.scalar_one_or_none()

        if not project:
            logger.info("Creating demo project 'CodeForge AI Playground'...")
            project = Project(
                id=uuid4(),
                owner_id=user.id,
                title="CodeForge AI Playground",
                description="Interactive multi-file coding workspace with AI Copilot.",
                language="python",
                visibility=ProjectVisibility.PUBLIC,
            )
            db.add(project)
            await db.commit()
            await db.refresh(project)

            # Files for project
            files = [
                ProjectFile(
                    project_id=project.id,
                    path="main.py",
                    name="main.py",
                    content="""import time

def calculate_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

if __name__ == '__main__':
    print("🚀 CodeForge AI Execution Sandbox")
    start = time.perf_counter()
    res = calculate_fibonacci(35)
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Fibonacci(35) = {res} in {elapsed:.2f}ms")
""",
                    is_directory=False,
                    language="python",
                ),
                ProjectFile(
                    project_id=project.id,
                    path="utils/helpers.py",
                    name="helpers.py",
                    content="""def format_time_ms(ms: float) -> str:
    return f"{ms:.2f} ms"
""",
                    is_directory=False,
                    language="python",
                ),
            ]
            for f in files:
                db.add(f)

        await db.commit()
        logger.info("✅ Database successfully seeded!")


if __name__ == "__main__":
    asyncio.run(seed_all())
