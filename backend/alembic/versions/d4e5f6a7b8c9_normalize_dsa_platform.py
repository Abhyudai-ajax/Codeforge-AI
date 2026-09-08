"""Normalize DSA problems and make submissions asynchronous.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
"""

import sqlalchemy as sa

from alembic import op

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    difficulty = sa.Enum("easy", "medium", "hard", name="problemdifficulty")
    submission_status = sa.Enum(
        "queued",
        "running",
        "accepted",
        "wrong_answer",
        "compilation_error",
        "runtime_error",
        "time_limit_exceeded",
        "memory_limit_exceeded",
        "failed",
        name="submissionstatus",
    )
    difficulty.create(op.get_bind(), checkfirst=True)
    submission_status.create(op.get_bind(), checkfirst=True)
    op.execute("UPDATE problems SET difficulty = lower(difficulty)")
    with op.batch_alter_table("problems") as batch:
        batch.alter_column(
            "difficulty",
            existing_type=sa.String(20),
            type_=difficulty,
            postgresql_using="difficulty::problemdifficulty",
        )
        batch.alter_column("test_cases", existing_type=sa.JSON(), nullable=True)
        batch.add_column(
            sa.Column("input_description", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("output_description", sa.Text(), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column("examples", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch.add_column(
            sa.Column(
                "supported_languages",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[\"python\"]'"),
            )
        )
        batch.add_column(sa.Column("editorial_md", sa.Text(), nullable=True))
        batch.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch.create_index("ix_problems_is_active", ["is_active"])
    op.create_table(
        "problem_tags",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
    )
    op.create_index("ix_problem_tags_name", "problem_tags", ["name"])
    op.create_table(
        "problem_tag_links",
        sa.Column(
            "problem_id",
            sa.UUID(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.UUID(),
            sa.ForeignKey("problem_tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "test_cases",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "problem_id",
            sa.UUID(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_test_cases_problem_public", "test_cases", ["problem_id", "is_public"])
    with op.batch_alter_table("submissions") as batch:
        batch.alter_column("code", existing_type=sa.Text(), nullable=True)
        batch.add_column(
            sa.Column("room_id", sa.UUID(), sa.ForeignKey("coding_rooms.id", ondelete="SET NULL"))
        )
        batch.add_column(sa.Column("source_code", sa.Text(), nullable=True))
        batch.add_column(sa.Column("memory_kb", sa.Integer()))
        batch.add_column(
            sa.Column("passed_test_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(
            sa.Column("total_test_count", sa.Integer(), nullable=False, server_default="0")
        )
        batch.add_column(sa.Column("score", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("output", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("error_output", sa.Text(), nullable=False, server_default=""))
        batch.add_column(sa.Column("completed_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE submissions SET source_code = code WHERE source_code IS NULL")
    op.execute(
        "UPDATE submissions SET status = CASE status WHEN 'Accepted' THEN 'accepted' WHEN 'Wrong Answer' THEN 'wrong_answer' WHEN 'Time Limit Exceeded' THEN 'time_limit_exceeded' WHEN 'Runtime Error' THEN 'runtime_error' WHEN 'Compile Error' THEN 'compilation_error' ELSE 'queued' END"
    )
    with op.batch_alter_table("submissions") as batch:
        batch.alter_column("source_code", nullable=False)
        batch.alter_column(
            "status",
            existing_type=sa.String(30),
            type_=submission_status,
            postgresql_using="status::submissionstatus",
            server_default="queued",
        )
    op.create_table(
        "user_problem_progress",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "problem_id",
            sa.UUID(),
            sa.ForeignKey("problems.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_submissions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_submissions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_solved_at", sa.DateTime(timezone=True)),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress"),
    )
    op.create_index("ix_user_problem_progress_user_id", "user_problem_progress", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_problem_progress")
    op.drop_table("test_cases")
    op.drop_table("problem_tag_links")
    op.drop_table("problem_tags")
    with op.batch_alter_table("submissions") as batch:
        for name in (
            "completed_at",
            "error_output",
            "output",
            "score",
            "total_test_count",
            "passed_test_count",
            "memory_kb",
            "source_code",
            "room_id",
        ):
            batch.drop_column(name)
    with op.batch_alter_table("problems") as batch:
        batch.drop_index("ix_problems_is_active")
        for name in (
            "is_active",
            "editorial_md",
            "supported_languages",
            "examples",
            "output_description",
            "input_description",
        ):
            batch.drop_column(name)
    sa.Enum(name="submissionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="problemdifficulty").drop(op.get_bind(), checkfirst=True)
