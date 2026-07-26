"""Database models and schemas

Import models here to ensure they are registered on the ORM metadata
and available to Alembic autogenerate.
"""

# Import models so that Base.metadata is populated for migrations
from app.models import user  # noqa: F401
