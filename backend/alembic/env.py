"""Alembic migration environment configuration"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, engine_from_config, pool

from alembic import context

# ``alembic -c alembic/alembic.ini`` executes this file without necessarily
# adding the backend directory to sys.path (notably on Windows entry points).
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
# Ensure models are imported so metadata includes all tables for autogenerate
import app.models  # noqa: F401
from app.core.config import settings
from app.core.database import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode"""
    # Allow overriding the URL from alembic Config (useful for autogenerate tests)
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode"""
    # Prefer sqlalchemy.url set in alembic Config; fall back to settings
    url = config.get_main_option("sqlalchemy.url") or settings.DATABASE_URL
    # Convert async URL to sync URL for alembic if needed
    url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
