"""
Database Configuration
SQLAlchemy setup with async support
"""

from sqlalchemy.ext.asyncio import (  # noqa: F401
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings


# Prepare async database URL (use asyncpg for PostgreSQL if not already set)
def _build_async_database_url(url: str) -> str:
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Create async engine
async_db_url = _build_async_database_url(settings.DATABASE_URL)
engine = create_async_engine(
    async_db_url,
    echo=settings.DATABASE_ECHO,
    future=True,
)


# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


# Base model for all ORM models
Base = declarative_base()


async def get_db():
    """Yield an async DB session for dependency injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create database tables from models' metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Dispose of the engine and close connections."""
    await engine.dispose()
