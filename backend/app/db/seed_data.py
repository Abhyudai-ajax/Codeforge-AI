"""Seed the database with the curated DSA catalog, a demo user, and a demo project.

Re-running the seeder is safe: existing problems are refreshed in place from
``app.db.problem_catalog`` rather than duplicated, so editing the catalog and
re-seeding brings an environment up to date.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, init_db
from app.db.problem_catalog import CATALOG, ProblemSpec
from app.models.problem import Problem, ProblemDifficulty, ProblemTag, TestCase
from app.models.project import Project, ProjectVisibility
from app.models.project_file import ProjectFile
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_data")

DEMO_USERNAME = "demo_dev"
DEMO_PASSWORD = "password123"
DEMO_PROJECT_TITLE = "CodeForge AI Playground"


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


async def seed_all() -> None:
    logger.info("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        user = await seed_demo_user(db)
        created, updated = await seed_problems(db)
        logger.info("Problems seeded: %d created, %d refreshed.", created, updated)
        await seed_demo_project(db, user)

    logger.info("Database successfully seeded with %d DSA problems.", len(CATALOG))


if __name__ == "__main__":
    asyncio.run(seed_all())
