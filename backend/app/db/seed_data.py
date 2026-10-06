"""Seed the database with the DSA catalog, roadmaps, contests, a demo user and project.

Re-running the seeder is safe: existing problems are refreshed in place from
``app.db.problem_catalog`` rather than duplicated, so editing the catalog and
re-seeding brings an environment up to date.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.db.problem_catalog import CATALOG, ProblemSpec
from app.models.contest import Contest, ContestProblem
from app.models.problem import Problem, ProblemDifficulty, ProblemTag, TestCase
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.roadmap import Roadmap, RoadmapStage, RoadmapStageProblem
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

DEMO_USERNAME = "demo_dev"
DEMO_PASSWORD = "password123"
DEMO_PROJECT_TITLE = "CodeForge AI Playground"

# (stage title, catalog categories) in the order a learner should tackle them.
DSA_MASTERY_STAGES: list[tuple[str, tuple[str, ...]]] = [
    ("Arrays & Hashing", ("arrays", "hashing")),
    ("Two Pointers & Sliding Window", ("two pointers", "sliding window")),
    ("Strings", ("strings",)),
    ("Stacks & Queues", ("stack", "queue", "design")),
    ("Linked Lists", ("linked list",)),
    ("Binary Search", ("binary search",)),
    ("Prefix Sums, Sorting & Bits", ("prefix sum", "sorting", "bit manipulation")),
    ("Heaps", ("heaps",)),
    ("Trees", ("trees",)),
    ("Graphs", ("graphs",)),
    ("Greedy", ("greedy",)),
    ("Backtracking", ("backtracking",)),
    ("Dynamic Programming", ("dynamic programming",)),
]

# (slug, title, start offset from now, duration, problem slugs).
DEMO_CONTESTS: list[tuple[str, str, timedelta, timedelta, tuple[str, ...]]] = [
    (
        "weekly-warmup",
        "Weekly Warm-up",
        timedelta(hours=-1),
        timedelta(days=7),
        ("two-sum", "valid-parentheses", "maximum-subarray", "number-of-islands"),
    ),
    (
        "algorithms-sprint",
        "Algorithms Sprint",
        timedelta(days=3),
        timedelta(hours=2),
        ("3sum", "coin-change", "course-schedule", "trapping-rain-water"),
    ),
    (
        "starter-round",
        "Starter Round",
        timedelta(days=-7),
        timedelta(hours=2),
        ("array-sum", "climbing-stairs", "reverse-linked-list"),
    ),
]


async def _resolve_tags(db: AsyncSession, names: set[str]) -> dict[str, ProblemTag]:
    """Fetch or create every tag up front.

    Resolving these before the seeding loop matters: creating a tag flushes the
    session, and a flush mid-loop would turn a freshly added Problem into a
    persistent row whose collections then lazy-load on assignment — illegal
    under asyncio.
    """
    normalized = {name.strip().lower() for name in names}
    existing = {
        tag.name: tag
        for tag in (
            await db.execute(select(ProblemTag).where(ProblemTag.name.in_(normalized)))
        ).scalars()
    }
    for name in sorted(normalized - set(existing)):
        tag = ProblemTag(name=name)
        db.add(tag)
        existing[name] = tag
    await db.flush()
    return existing


def _apply(problem: Problem, spec: ProblemSpec) -> None:
    """Copy every catalog-owned field onto the ORM row."""
    problem.title = spec.title
    problem.difficulty = ProblemDifficulty(spec.difficulty)
    problem.description_md = spec.description_md
    problem.input_description = spec.input_description
    problem.output_description = spec.output_description
    problem.constraints = list(spec.constraints)
    problem.examples = [
        {"input": stdin, "output": expected} for stdin, expected in spec.cases[: spec.sample_count]
    ]
    problem.starter_code = spec.starter_code
    problem.supported_languages = spec.supported_languages
    problem.editorial_md = spec.editorial
    problem.is_active = True
    problem.test_cases = [
        TestCase(
            input_data=stdin,
            expected_output=expected,
            is_public=index < spec.sample_count,
            order=index,
        )
        for index, (stdin, expected) in enumerate(spec.cases)
    ]


async def seed_problems(db: AsyncSession) -> tuple[int, int]:
    """Insert missing problems and refresh existing ones. Returns (created, updated)."""
    tags = await _resolve_tags(db, {spec.category for spec in CATALOG})
    # `tags` and `test_cases` are selectin-loaded, so existing rows arrive with
    # their collections populated and can be reassigned without further IO.
    existing = {
        problem.slug: problem
        for problem in (
            await db.execute(
                select(Problem).where(Problem.slug.in_([spec.slug for spec in CATALOG]))
            )
        ).scalars()
    }

    created = updated = 0
    for spec in CATALOG:
        problem = existing.get(spec.slug)
        if problem is None:
            problem = Problem(id=uuid4(), slug=spec.slug)
            db.add(problem)
            created += 1
        else:
            updated += 1
        _apply(problem, spec)
        problem.tags = [tags[spec.category.strip().lower()]]
    await db.commit()
    return created, updated


async def seed_demo_user(db: AsyncSession) -> User:
    user = (
        await db.execute(select(User).where(User.username == DEMO_USERNAME))
    ).scalar_one_or_none()
    if user:
        return user

    from app.core.security import hash_password

    logger.info("Creating demo user %r...", DEMO_USERNAME)
    user = User(
        id=uuid4(),
        username=DEMO_USERNAME,
        email="demo@codeforge.ai",
        hashed_password=hash_password(DEMO_PASSWORD),
        full_name="Alex Rivera",
        role=UserRole.USER,
        bio="FAANG Senior Software Engineer | Algorithmic Problem Solver",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def seed_demo_project(db: AsyncSession, owner: User) -> None:
    project = (
        await db.execute(select(Project).where(Project.title == DEMO_PROJECT_TITLE))
    ).scalar_one_or_none()
    if project:
        return

    logger.info("Creating demo project %r...", DEMO_PROJECT_TITLE)
    project = Project(
        id=uuid4(),
        owner_id=owner.id,
        title=DEMO_PROJECT_TITLE,
        description="Interactive multi-file coding workspace with AI Copilot.",
        language="python",
        visibility=ProjectVisibility.PUBLIC,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    db.add_all(
        [
            ProjectFile(
                project_id=project.id,
                path="main.py",
                name="main.py",
                content=(
                    "import time\n\n\n"
                    "def calculate_fibonacci(n: int) -> int:\n"
                    "    if n <= 1:\n"
                    "        return n\n"
                    "    a, b = 0, 1\n"
                    "    for _ in range(2, n + 1):\n"
                    "        a, b = b, a + b\n"
                    "    return b\n\n\n"
                    'if __name__ == "__main__":\n'
                    '    print("CodeForge AI Execution Sandbox")\n'
                    "    start = time.perf_counter()\n"
                    "    result = calculate_fibonacci(35)\n"
                    "    elapsed = (time.perf_counter() - start) * 1000\n"
                    '    print(f"Fibonacci(35) = {result} in {elapsed:.2f}ms")\n'
                ),
                is_directory=False,
                language="python",
            ),
            ProjectFile(
                project_id=project.id,
                path="utils/helpers.py",
                name="helpers.py",
                content='def format_time_ms(ms: float) -> str:\n    return f"{ms:.2f} ms"\n',
                is_directory=False,
                language="python",
            ),
        ]
    )
    await db.commit()


def _slugify(title: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in title.lower()).split())


async def seed_roadmaps(db: AsyncSession) -> None:
    """Create the built-in roadmaps from the catalog if they don't exist yet."""
    problems = {p.slug: p for p in (await db.execute(select(Problem))).scalars()}
    by_category: dict[str, list[Problem]] = {}
    for spec in CATALOG:
        if spec.slug in problems:
            by_category.setdefault(spec.category.strip().lower(), []).append(problems[spec.slug])

    # Each stage is tagged with its first category for the progress breakdown.
    full_stages = [
        (title, cats[0], [p for c in cats for p in by_category.get(c, [])])
        for title, cats in DSA_MASTERY_STAGES
    ]
    easy_stages = [
        (title, category, [p for p in stage if p.difficulty == ProblemDifficulty.EASY])
        for title, category, stage in full_stages
    ]
    roadmaps = [
        (
            "dsa-mastery",
            "DSA Mastery",
            "Every problem in the catalog, grouped by topic and ordered from fundamentals "
            "to dynamic programming.",
            True,
            full_stages,
        ),
        (
            "beginner-path",
            "Beginner Path",
            "Only the easy problems, topic by topic. A gentle start before DSA Mastery.",
            False,
            easy_stages,
        ),
    ]

    existing = set((await db.execute(select(Roadmap.slug))).scalars())
    for order, (slug, title, description, is_default, stages) in enumerate(roadmaps):
        if slug in existing:
            continue
        roadmap = Roadmap(
            slug=slug,
            title=title,
            description_md=description,
            is_published=True,
            is_default=is_default,
            order=order,
        )
        non_empty = [stage for stage in stages if stage[2]]
        roadmap.stages = [
            RoadmapStage(
                title=stage_title,
                slug=_slugify(stage_title),
                category_name=category,
                order=stage_order,
                problems=[
                    RoadmapStageProblem(problem_id=problem.id, order=i)
                    for i, problem in enumerate(stage_problems)
                ],
            )
            for stage_order, (stage_title, category, stage_problems) in enumerate(non_empty)
        ]
        db.add(roadmap)
        logger.info("Created roadmap %r with %d stages.", slug, len(roadmap.stages))
    await db.commit()


async def seed_contests(db: AsyncSession, owner: User) -> None:
    """Create demo contests (running, upcoming, ended) if they don't exist yet."""
    problems = {p.slug: p for p in (await db.execute(select(Problem))).scalars()}
    existing = set((await db.execute(select(Contest.slug))).scalars())
    now = datetime.now(UTC)
    for slug, title, start_offset, duration, problem_slugs in DEMO_CONTESTS:
        if slug in existing:
            continue
        start = now + start_offset
        contest = Contest(
            slug=slug,
            title=title,
            description_md=f"{title}: solve as many problems as you can before time runs out.",
            start_time=start,
            end_time=start + duration,
            is_published=True,
            created_by_id=owner.id,
        )
        contest.problems = [
            ContestProblem(
                problem_id=problems[ps].id, order=i, label=chr(ord("A") + i), points=100 * (i + 1)
            )
            for i, ps in enumerate(p for p in problem_slugs if p in problems)
        ]
        db.add(contest)
        logger.info("Created contest %r.", slug)
    await db.commit()


async def seed_all() -> None:
    logger.info("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        user = await seed_demo_user(db)
        created, updated = await seed_problems(db)
        logger.info("Problems seeded: %d created, %d refreshed.", created, updated)
        await seed_demo_project(db, user)
        await seed_roadmaps(db)
        await seed_contests(db, user)

    logger.info("Database successfully seeded with %d DSA problems.", len(CATALOG))


if __name__ == "__main__":
    asyncio.run(seed_all())
