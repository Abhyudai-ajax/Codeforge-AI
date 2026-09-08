"""Create contests and leaderboards tables.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-27 12:15:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description_md", sa.Text(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_by_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_contests_is_published"), "contests", ["is_published"], unique=False)
    op.create_index(op.f("ix_contests_slug"), "contests", ["slug"], unique=True)
    op.create_index(op.f("ix_contests_start_time"), "contests", ["start_time"], unique=False)
    op.create_index(op.f("ix_contests_end_time"), "contests", ["end_time"], unique=False)

    op.create_table(
        "contest_problems",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contest_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.UUID(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=10), nullable=False),
        sa.ForeignKeyConstraint(["contest_id"], ["contests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contest_id", "problem_id", name="uq_contest_problem"),
        sa.UniqueConstraint("contest_id", "label", name="uq_contest_label"),
    )

    op.create_table(
        "contest_registrations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contest_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contest_id"], ["contests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contest_id", "user_id", name="uq_contest_user_registration"),
    )

    op.create_table(
        "contest_submissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contest_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.UUID(), nullable=False),
        sa.Column("submission_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["contest_id"], ["contests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contest_participants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("contest_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("total_penalty", sa.Integer(), nullable=False),
        sa.Column("problems_solved", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["contest_id"], ["contests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contest_id", "user_id", name="uq_contest_participant"),
    )
    op.create_index(
        "idx_contest_leaderboard",
        "contest_participants",
        ["contest_id", sa.text("total_score DESC"), sa.text("total_penalty ASC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_contest_leaderboard", table_name="contest_participants")
    op.drop_table("contest_participants")
    op.drop_table("contest_submissions")
    op.drop_table("contest_registrations")
    op.drop_table("contest_problems")
    op.drop_index(op.f("ix_contests_end_time"), table_name="contests")
    op.drop_index(op.f("ix_contests_start_time"), table_name="contests")
    op.drop_index(op.f("ix_contests_slug"), table_name="contests")
    op.drop_index(op.f("ix_contests_is_published"), table_name="contests")
    op.drop_table("contests")
