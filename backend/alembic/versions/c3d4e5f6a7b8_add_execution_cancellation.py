"""Add cancellable execution state.

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
"""

from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE executionstatus ADD VALUE IF NOT EXISTS 'cancelled'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be safely removed in-place.
    pass
