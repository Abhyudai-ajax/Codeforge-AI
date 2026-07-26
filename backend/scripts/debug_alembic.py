"""Debug Alembic autogenerate behavior.

Prints:
- registered tables on Base.metadata
- comparison diffs from Alembic autogenerate
"""

import sys
from pathlib import Path
from pprint import pformat

# Ensure backend package is importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from sqlalchemy import create_engine

import app.models  # ensure models registered
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

# Import project metadata and models
from app.core.database import Base

print("Registered tables:", list(Base.metadata.tables.keys()))

# Use an in-memory SQLite DB for autogenerate compare
engine = create_engine("sqlite:///:memory:")
with engine.connect() as conn:
    ctx = MigrationContext.configure(conn)
    diffs = compare_metadata(ctx, Base.metadata)
    print("Autogenerate diffs:\n", pformat(diffs))
