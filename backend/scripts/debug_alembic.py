"""Debug Alembic autogenerate behavior.

Prints:
- registered tables on Base.metadata
- comparison diffs from Alembic autogenerate
"""

import importlib
import sys
from pathlib import Path
from pprint import pformat

from sqlalchemy import create_engine

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

# Ensure backend package is importable
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


def main() -> None:
    importlib.import_module("app.models")  # ensure models registered
    base_module = importlib.import_module("app.core.database")
    Base = getattr(base_module, "Base")

    print("Registered tables:", list(Base.metadata.tables.keys()))

    # Use an in-memory SQLite DB for autogenerate compare
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        diffs = compare_metadata(ctx, Base.metadata)
        print("Autogenerate diffs:\n", pformat(diffs))


if __name__ == "__main__":
    main()
