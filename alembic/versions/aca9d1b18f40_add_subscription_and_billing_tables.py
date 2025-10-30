"""add_subscription_and_billing_tables

Revision ID: aca9d1b18f40
Revises: ce3adb6ef385
Create Date: 2025-10-30 13:37:00.676016

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "aca9d1b18f40"
down_revision: Union[str, Sequence[str], None] = "ce3adb6ef385"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add stripe_customer_id to users table
    op.add_column(
        "users",
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
    )
    op.create_index("idx_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=True)

    # Create subscriptions table
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("plan_tier", sa.String(50), nullable=False),
        sa.Column("billing_period", sa.String(20), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("trial_end", sa.DateTime(), nullable=True),
        sa.Column("current_period_start", sa.DateTime(), nullable=True),
        sa.Column("current_period_end", sa.DateTime(), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=True, default=False),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
        sa.UniqueConstraint("stripe_subscription_id"),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index(
        "idx_subscriptions_stripe_subscription_id",
        "subscriptions",
        ["stripe_subscription_id"],
    )
    op.create_index(
        "idx_subscriptions_stripe_customer_id",
        "subscriptions",
        ["stripe_customer_id"],
    )
    op.create_index("idx_subscriptions_status", "subscriptions", ["status"])
    op.create_index("idx_subscriptions_plan_tier", "subscriptions", ["plan_tier"])

    # Create usage_records table
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=False),
        sa.Column("api_calls", sa.Integer(), nullable=True, default=0),
        sa.Column("videos_processed", sa.Integer(), nullable=True, default=0),
        sa.Column("matches_performed", sa.Integer(), nullable=True, default=0),
        sa.Column("storage_used_mb", sa.Float(), nullable=True, default=0),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("stripe_usage_record_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
    )
    op.create_index("idx_usage_records_subscription_id", "usage_records", ["subscription_id"])
    op.create_index(
        "idx_usage_records_period",
        "usage_records",
        ["period_start", "period_end"],
    )

    # Create invoices table
    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("subscription_id", sa.Integer(), nullable=True),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=True),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("amount_due", sa.Integer(), nullable=True),
        sa.Column("amount_paid", sa.Integer(), nullable=True),
        sa.Column("amount_remaining", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True, default="usd"),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("paid", sa.Boolean(), nullable=True, default=False),
        sa.Column("invoice_pdf", sa.String(500), nullable=True),
        sa.Column("hosted_invoice_url", sa.String(500), nullable=True),
        sa.Column("created", sa.DateTime(), nullable=True),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["subscription_id"], ["subscriptions.id"]),
        sa.UniqueConstraint("stripe_invoice_id"),
    )
    op.create_index("idx_invoices_user_id", "invoices", ["user_id"])
    op.create_index("idx_invoices_subscription_id", "invoices", ["subscription_id"])
    op.create_index("idx_invoices_stripe_invoice_id", "invoices", ["stripe_invoice_id"])
    op.create_index("idx_invoices_status", "invoices", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes and tables in reverse order
    op.drop_index("idx_invoices_status", table_name="invoices")
    op.drop_index("idx_invoices_stripe_invoice_id", table_name="invoices")
    op.drop_index("idx_invoices_subscription_id", table_name="invoices")
    op.drop_index("idx_invoices_user_id", table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("idx_usage_records_period", table_name="usage_records")
    op.drop_index("idx_usage_records_subscription_id", table_name="usage_records")
    op.drop_table("usage_records")

    op.drop_index("idx_subscriptions_plan_tier", table_name="subscriptions")
    op.drop_index("idx_subscriptions_status", table_name="subscriptions")
    op.drop_index("idx_subscriptions_stripe_customer_id", table_name="subscriptions")
    op.drop_index("idx_subscriptions_stripe_subscription_id", table_name="subscriptions")
    op.drop_index("idx_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("idx_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "stripe_customer_id")
