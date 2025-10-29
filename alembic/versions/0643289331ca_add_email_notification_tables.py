"""add_email_notification_tables

Revision ID: 0643289331ca
Revises: e0ae37366ae4
Create Date: 2025-10-28 21:58:53.824330

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0643289331ca"
down_revision: Union[str, Sequence[str], None] = "e0ae37366ae4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create email_preferences table
    op.create_table(
        "email_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("receive_welcome", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("receive_password_reset", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("receive_security_alerts", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("receive_match_found", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "receive_processing_complete", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("receive_quota_warnings", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("receive_api_key_generated", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "receive_feature_announcements", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column("receive_tips_tricks", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("receive_case_studies", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("receive_daily_digest", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("receive_weekly_digest", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("preferred_language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("unsubscribed_at", sa.DateTime(), nullable=True),
        sa.Column("unsubscribe_token", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("unsubscribe_token"),
    )
    op.create_index("idx_email_preferences_user_id", "email_preferences", ["user_id"])

    # Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("html_body", sa.Text(), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("variables", sa.Text(), nullable=True),
        sa.Column("variant", sa.String(length=20), nullable=False, server_default="A"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("idx_email_templates_name", "email_templates", ["name"])
    op.create_index("idx_email_templates_category", "email_templates", ["category"])
    op.create_index("idx_email_templates_language", "email_templates", ["language"])

    # Create email_logs table
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("template_name", sa.String(length=100), nullable=True),
        sa.Column("template_variant", sa.String(length=20), nullable=True),
        sa.Column("subject", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("opened_at", sa.DateTime(), nullable=True),
        sa.Column("clicked_at", sa.DateTime(), nullable=True),
        sa.Column("open_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("campaign_id", sa.String(length=100), nullable=True),
        sa.Column("ab_test_group", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_email_logs_user_id", "email_logs", ["user_id"])
    op.create_index("idx_email_logs_status", "email_logs", ["status"])
    op.create_index("idx_email_logs_category", "email_logs", ["category"])
    op.create_index("idx_email_logs_sent_at", "email_logs", ["sent_at"])
    op.create_index("idx_email_logs_campaign_id", "email_logs", ["campaign_id"])

    # Create email_campaigns table
    op.create_table(
        "email_campaigns",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="marketing"),
        sa.Column("scheduled_at", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("ab_test_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ab_test_variants", sa.Text(), nullable=True),
        sa.Column("ab_test_split_percentage", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("target_segment", sa.String(length=100), nullable=True),
        sa.Column("total_recipients", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_sent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_opened", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_clicked", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("emails_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_email_campaigns_status", "email_campaigns", ["status"])
    op.create_index("idx_email_campaigns_scheduled_at", "email_campaigns", ["scheduled_at"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_index("idx_email_campaigns_scheduled_at", "email_campaigns")
    op.drop_index("idx_email_campaigns_status", "email_campaigns")
    op.drop_table("email_campaigns")

    op.drop_index("idx_email_logs_campaign_id", "email_logs")
    op.drop_index("idx_email_logs_sent_at", "email_logs")
    op.drop_index("idx_email_logs_category", "email_logs")
    op.drop_index("idx_email_logs_status", "email_logs")
    op.drop_index("idx_email_logs_user_id", "email_logs")
    op.drop_table("email_logs")

    op.drop_index("idx_email_templates_language", "email_templates")
    op.drop_index("idx_email_templates_category", "email_templates")
    op.drop_index("idx_email_templates_name", "email_templates")
    op.drop_table("email_templates")

    op.drop_index("idx_email_preferences_user_id", "email_preferences")
    op.drop_table("email_preferences")
