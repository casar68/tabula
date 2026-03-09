"""add users table and multi-user columns

Revision ID: a1b2c3d4e5f6
Revises: dd9d906eb477
Create Date: 2026-03-09 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "dd9d906eb477"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users table, user_id FK on documents/templates, is_shared on templates."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=150), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    # Add user_id to documents
    op.add_column("documents", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_documents_user_id"), "documents", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_documents_user_id",
        "documents",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add user_id and is_shared to templates
    op.add_column("templates", sa.Column("user_id", sa.Uuid(), nullable=True))
    op.add_column(
        "templates",
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(op.f("ix_templates_user_id"), "templates", ["user_id"], unique=False)
    op.create_foreign_key(
        "fk_templates_user_id",
        "templates",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove multi-user columns and users table."""
    # Drop templates FK and columns
    op.drop_constraint("fk_templates_user_id", "templates", type_="foreignkey")
    op.drop_index(op.f("ix_templates_user_id"), table_name="templates")
    op.drop_column("templates", "is_shared")
    op.drop_column("templates", "user_id")

    # Drop documents FK and columns
    op.drop_constraint("fk_documents_user_id", "documents", type_="foreignkey")
    op.drop_index(op.f("ix_documents_user_id"), table_name="documents")
    op.drop_column("documents", "user_id")

    # Drop users table
    op.drop_table("users")
