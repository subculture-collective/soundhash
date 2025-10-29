"""add_multi_tenant_support

Revision ID: 3008b188cd54
Revises: 0643289331ca
Create Date: 2025-10-29 04:06:39.212571

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "3008b188cd54"
down_revision = "0643289331ca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("admin_email", sa.String(length=255), nullable=False),
        sa.Column("admin_name", sa.String(length=255), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("primary_color", sa.String(length=7), nullable=True),
        sa.Column("custom_domain", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("plan_tier", sa.String(length=50), nullable=True),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("max_api_calls_per_month", sa.Integer(), nullable=True),
        sa.Column("max_storage_gb", sa.Integer(), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        sa.UniqueConstraint("custom_domain"),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"], unique=False)
    op.create_index("idx_tenants_custom_domain", "tenants", ["custom_domain"], unique=False)
    op.create_index("idx_tenants_is_active", "tenants", ["is_active"], unique=False)

    # Add tenant_id and role to users table
    op.add_column("users", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("users", sa.Column("role", sa.String(length=50), nullable=True, server_default="member"))
    op.create_foreign_key("fk_users_tenant_id", "users", "tenants", ["tenant_id"], ["id"])
    op.create_index("idx_users_tenant_id", "users", ["tenant_id"], unique=False)

    # Add tenant_id and scopes to api_keys table
    op.add_column("api_keys", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.add_column("api_keys", sa.Column("scopes", sa.JSON(), nullable=True))
    op.create_foreign_key("fk_api_keys_tenant_id", "api_keys", "tenants", ["tenant_id"], ["id"])
    op.create_index("idx_api_keys_tenant_id", "api_keys", ["tenant_id"], unique=False)

    # Add tenant_id to channels table
    op.add_column("channels", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_channels_tenant_id", "channels", "tenants", ["tenant_id"], ["id"])
    op.create_index("idx_channels_tenant_id", "channels", ["tenant_id"], unique=False)

    # Add tenant_id to videos table
    op.add_column("videos", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_videos_tenant_id", "videos", "tenants", ["tenant_id"], ["id"])
    op.create_index("idx_videos_tenant_id", "videos", ["tenant_id"], unique=False)

    # Add tenant_id to audio_fingerprints table
    op.add_column("audio_fingerprints", sa.Column("tenant_id", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_audio_fingerprints_tenant_id", "audio_fingerprints", "tenants", ["tenant_id"], ["id"])
    op.create_index("idx_fingerprints_tenant_id", "audio_fingerprints", ["tenant_id"], unique=False)
    op.create_index("idx_fingerprints_tenant_hash", "audio_fingerprints", ["tenant_id", "fingerprint_hash"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove indexes and foreign keys from audio_fingerprints
    op.drop_index("idx_fingerprints_tenant_hash", table_name="audio_fingerprints")
    op.drop_index("idx_fingerprints_tenant_id", table_name="audio_fingerprints")
    op.drop_constraint("fk_audio_fingerprints_tenant_id", "audio_fingerprints", type_="foreignkey")
    op.drop_column("audio_fingerprints", "tenant_id")

    # Remove indexes and foreign keys from videos
    op.drop_index("idx_videos_tenant_id", table_name="videos")
    op.drop_constraint("fk_videos_tenant_id", "videos", type_="foreignkey")
    op.drop_column("videos", "tenant_id")

    # Remove indexes and foreign keys from channels
    op.drop_index("idx_channels_tenant_id", table_name="channels")
    op.drop_constraint("fk_channels_tenant_id", "channels", type_="foreignkey")
    op.drop_column("channels", "tenant_id")

    # Remove tenant_id and scopes from api_keys
    op.drop_index("idx_api_keys_tenant_id", table_name="api_keys")
    op.drop_constraint("fk_api_keys_tenant_id", "api_keys", type_="foreignkey")
    op.drop_column("api_keys", "scopes")
    op.drop_column("api_keys", "tenant_id")

    # Remove tenant_id and role from users
    op.drop_index("idx_users_tenant_id", table_name="users")
    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
    op.drop_column("users", "role")
    op.drop_column("users", "tenant_id")

    # Drop tenants table
    op.drop_index("idx_tenants_is_active", table_name="tenants")
    op.drop_index("idx_tenants_custom_domain", table_name="tenants")
    op.drop_index("idx_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
