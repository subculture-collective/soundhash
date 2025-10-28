"""add_user_and_api_key_models

Revision ID: d4a7e3b9c2f1
Revises: b9532a7d8c7a
Create Date: 2025-10-27 20:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4a7e3b9c2f1"
down_revision: Union[str, Sequence[str], None] = "b9532a7d8c7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add users and api_keys tables."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_users_username", "users", ["username"], unique=True)
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_is_active", "users", ["is_active"], unique=False)

    # Create api_keys table
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("key_name", sa.String(length=100), nullable=False),
        sa.Column("key_hash", sa.String(length=255), nullable=False),
        sa.Column("key_prefix", sa.String(length=20), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"], unique=False)
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_index("idx_api_keys_is_active", "api_keys", ["is_active"], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove users and api_keys tables."""
    # Drop api_keys table
    op.drop_index("idx_api_keys_is_active", table_name="api_keys")
    op.drop_index("idx_api_keys_key_hash", table_name="api_keys")
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")

    # Drop users table
    op.drop_index("idx_users_is_active", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_table("users")
