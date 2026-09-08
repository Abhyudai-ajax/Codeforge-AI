"""Add coding rooms and room memberships.

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
"""

import sqlalchemy as sa

from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    member_role = sa.Enum("owner", "editor", "viewer", name="roommemberrole")
    member_role.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "coding_rooms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("document", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coding_rooms_owner_id", "coding_rooms", ["owner_id"])
    op.create_index("ix_coding_rooms_public_created", "coding_rooms", ["is_public", "created_at"])
    op.create_table(
        "room_memberships",
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", member_role, nullable=False, server_default="editor"),
        sa.Column(
            "joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["room_id"], ["coding_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("room_id", "user_id"),
    )
    op.create_index("ix_room_memberships_user_id", "room_memberships", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_room_memberships_user_id", table_name="room_memberships")
    op.drop_table("room_memberships")
    op.drop_index("ix_coding_rooms_public_created", table_name="coding_rooms")
    op.drop_index("ix_coding_rooms_owner_id", table_name="coding_rooms")
    op.drop_table("coding_rooms")
    sa.Enum("owner", "editor", "viewer", name="roommemberrole").drop(op.get_bind(), checkfirst=True)
