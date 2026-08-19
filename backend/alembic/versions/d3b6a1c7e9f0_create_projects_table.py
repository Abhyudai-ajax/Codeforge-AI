"""create projects table

Revision ID: d3b6a1c7e9f0
Revises: c2f0c2d4e676
Create Date: 2026-08-05 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "d3b6a1c7e9f0"
down_revision = "c2f0c2d4e676"
branch_labels = None
depends_on = None


def upgrade() -> None:
    project_visibility = sa.Enum("private", "public", name="projectvisibility")
    project_visibility.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "owner_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("language", sa.String(length=50), nullable=False),
        sa.Column(
            "visibility",
            project_visibility,
            nullable=False,
            server_default="private",
        ),
        sa.Column("github_repo", sa.String(length=500), nullable=True),
        sa.Column("github_branch", sa.String(length=100), nullable=True),
        sa.Column("stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("forks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_projects_owner_visibility"),
        "projects",
        ["owner_id", "visibility"],
        unique=False,
    )
    op.create_index(
        op.f("ix_projects_owner_id"),
        "projects",
        ["owner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_projects_title"),
        "projects",
        ["title"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_title"), table_name="projects")
    op.drop_index(op.f("ix_projects_owner_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_owner_visibility"), table_name="projects")
    op.drop_table("projects")
    project_visibility = sa.Enum("private", "public", name="projectvisibility")
    project_visibility.drop(op.get_bind(), checkfirst=True)
