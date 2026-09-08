"""Add asynchronous isolated execution jobs.

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
"""

import sqlalchemy as sa

from alembic import op

revision = "b1c2d3e4f5a6"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    status = sa.Enum(
        "queued",
        "running",
        "completed",
        "compilation_error",
        "runtime_error",
        "timeout",
        "memory_limit",
        "failed",
        name="executionstatus",
    )
    status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "execution_jobs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("project_id", sa.UUID(), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("room_id", sa.UUID(), sa.ForeignKey("coding_rooms.id", ondelete="SET NULL")),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("stdin", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", status, nullable=False, server_default="queued"),
        sa.Column("stdout", sa.Text(), nullable=False, server_default=""),
        sa.Column("stderr", sa.Text(), nullable=False, server_default=""),
        sa.Column("exit_code", sa.Integer()),
        sa.Column("execution_time_ms", sa.Integer()),
        sa.Column("memory_kb", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_execution_jobs_user_id", "execution_jobs", ["user_id"])
    op.create_index("ix_execution_jobs_user_created", "execution_jobs", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_table("execution_jobs")
    sa.Enum(name="executionstatus").drop(op.get_bind(), checkfirst=True)
