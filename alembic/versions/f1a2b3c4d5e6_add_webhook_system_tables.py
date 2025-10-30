"""add_webhook_system_tables

Revision ID: f1a2b3c4d5e6
Revises: e5f8a2b3d4c1
Create Date: 2025-10-30 22:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e5f8a2b3d4c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add webhook system tables."""
    
    # Create webhooks table
    op.create_table(
        "webhooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True),
        sa.Column("custom_headers", sa.JSON(), nullable=True),
        sa.Column("total_deliveries", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("successful_deliveries", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("failed_deliveries", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("last_delivery_at", sa.DateTime(), nullable=True),
        sa.Column("last_success_at", sa.DateTime(), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create webhook_events table
    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_data", sa.JSON(), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("resource_type", sa.String(length=100), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create webhook_deliveries table
    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("webhook_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("request_headers", sa.JSON(), nullable=True),
        sa.Column("request_body", sa.Text(), nullable=True),
        sa.Column("response_status_code", sa.Integer(), nullable=True),
        sa.Column("response_headers", sa.JSON(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["event_id"], ["webhook_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    
    # Create indexes for webhooks
    op.create_index("idx_webhooks_user_id", "webhooks", ["user_id"], unique=False)
    op.create_index("idx_webhooks_tenant_id", "webhooks", ["tenant_id"], unique=False)
    op.create_index("idx_webhooks_is_active", "webhooks", ["is_active"], unique=False)
    
    # Create indexes for webhook_events
    op.create_index("idx_webhook_events_event_type", "webhook_events", ["event_type"], unique=False)
    op.create_index("idx_webhook_events_resource", "webhook_events", ["resource_type", "resource_id"], unique=False)
    op.create_index("idx_webhook_events_processed", "webhook_events", ["processed"], unique=False)
    op.create_index("idx_webhook_events_created_at", "webhook_events", ["created_at"], unique=False)
    
    # Create indexes for webhook_deliveries
    op.create_index("idx_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"], unique=False)
    op.create_index("idx_webhook_deliveries_event_id", "webhook_deliveries", ["event_id"], unique=False)
    op.create_index("idx_webhook_deliveries_status", "webhook_deliveries", ["status"], unique=False)
    op.create_index("idx_webhook_deliveries_next_retry", "webhook_deliveries", ["next_retry_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema - remove webhook system tables."""
    
    # Drop indexes
    op.drop_index("idx_webhook_deliveries_next_retry", table_name="webhook_deliveries")
    op.drop_index("idx_webhook_deliveries_status", table_name="webhook_deliveries")
    op.drop_index("idx_webhook_deliveries_event_id", table_name="webhook_deliveries")
    op.drop_index("idx_webhook_deliveries_webhook_id", table_name="webhook_deliveries")
    
    op.drop_index("idx_webhook_events_created_at", table_name="webhook_events")
    op.drop_index("idx_webhook_events_processed", table_name="webhook_events")
    op.drop_index("idx_webhook_events_resource", table_name="webhook_events")
    op.drop_index("idx_webhook_events_event_type", table_name="webhook_events")
    
    op.drop_index("idx_webhooks_is_active", table_name="webhooks")
    op.drop_index("idx_webhooks_tenant_id", table_name="webhooks")
    op.drop_index("idx_webhooks_user_id", table_name="webhooks")
    
    # Drop tables
    op.drop_table("webhook_deliveries")
    op.drop_table("webhook_events")
    op.drop_table("webhooks")
