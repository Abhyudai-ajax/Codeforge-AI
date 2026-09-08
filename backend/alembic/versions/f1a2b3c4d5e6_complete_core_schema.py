"""Complete the core schema for OAuth, workspaces, and DSA submissions.

Revision ID: f1a2b3c4d5e6
Revises: d3b6a1c7e9f0
"""

import sqlalchemy as sa

from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "d3b6a1c7e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("hashed_password", existing_type=sa.String(255), nullable=True)
        batch_op.add_column(sa.Column("github_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("github_username", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_users_github_id", ["github_id"], unique=True)

    op.create_table(
        "project_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("is_directory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("language", sa.String(length=30), nullable=False, server_default="python"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "path", name="ix_project_files_proj_path"),
    )
    op.create_index("ix_project_files_project_id", "project_files", ["project_id"])

    op.create_table(
        "problems",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False, server_default="Easy"),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="Arrays"),
        sa.Column("description_md", sa.Text(), nullable=False),
        sa.Column("starter_code", sa.JSON(), nullable=False),
        sa.Column("test_cases", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("time_limit_ms", sa.Integer(), nullable=False, server_default="2000"),
        sa.Column("memory_limit_mb", sa.Integer(), nullable=False, server_default="256"),
        sa.Column("acceptance_rate", sa.Float(), nullable=False, server_default="65"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_problems_slug", "problems", ["slug"], unique=True)
    op.create_index("ix_problems_title", "problems", ["title"])
    op.create_index("ix_problems_difficulty", "problems", ["difficulty"])
    op.create_index("ix_problems_category", "problems", ["category"])

    op.create_table(
        "submissions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.UUID(), nullable=False),
        sa.Column("language", sa.String(length=30), nullable=False, server_default="python"),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="Pending"),
        sa.Column("passed_test_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_test_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("runtime_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("memory_mb", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submissions_user_id", "submissions", ["user_id"])
    op.create_index("ix_submissions_problem_id", "submissions", ["problem_id"])
    op.create_index(
        "ix_submissions_user_problem_created",
        "submissions",
        ["user_id", "problem_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_submissions_user_problem_created", table_name="submissions")
    op.drop_index("ix_submissions_problem_id", table_name="submissions")
    op.drop_index("ix_submissions_user_id", table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_problems_category", table_name="problems")
    op.drop_index("ix_problems_difficulty", table_name="problems")
    op.drop_index("ix_problems_title", table_name="problems")
    op.drop_index("ix_problems_slug", table_name="problems")
    op.drop_table("problems")
    op.drop_index("ix_project_files_project_id", table_name="project_files")
    op.drop_table("project_files")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_github_id")
        batch_op.drop_column("github_username")
        batch_op.drop_column("github_id")
        batch_op.alter_column("hashed_password", existing_type=sa.String(255), nullable=False)
