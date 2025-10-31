"""add monetization tables

Revision ID: m1a2b3c4d5e6
Revises: f1a2b3c4d5e6
Create Date: 2025-10-31 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'm1a2b3c4d5e6'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create affiliate_programs table
    op.create_table(
        'affiliate_programs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('affiliate_code', sa.String(length=50), nullable=False),
        sa.Column('affiliate_name', sa.String(length=255), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=False),
        sa.Column('commission_duration_months', sa.Integer(), nullable=True),
        sa.Column('is_lifetime_commission', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('total_referrals', sa.Integer(), nullable=True),
        sa.Column('total_conversions', sa.Integer(), nullable=True),
        sa.Column('total_revenue_generated', sa.Integer(), nullable=True),
        sa.Column('total_commission_earned', sa.Integer(), nullable=True),
        sa.Column('total_commission_paid', sa.Integer(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_email', sa.String(length=255), nullable=True),
        sa.Column('payment_details', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('affiliate_code')
    )
    op.create_index('idx_affiliate_programs_user_id', 'affiliate_programs', ['user_id'])
    op.create_index('idx_affiliate_programs_code', 'affiliate_programs', ['affiliate_code'])
    op.create_index('idx_affiliate_programs_status', 'affiliate_programs', ['status'])

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('referrer_user_id', sa.Integer(), nullable=True),
        sa.Column('affiliate_id', sa.Integer(), nullable=True),
        sa.Column('referred_user_id', sa.Integer(), nullable=False),
        sa.Column('referral_code', sa.String(length=50), nullable=False),
        sa.Column('referral_source', sa.String(length=100), nullable=True),
        sa.Column('referral_campaign', sa.String(length=100), nullable=True),
        sa.Column('landing_page', sa.String(length=500), nullable=True),
        sa.Column('converted', sa.Boolean(), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(length=50), nullable=True),
        sa.Column('reward_amount', sa.Integer(), nullable=True),
        sa.Column('reward_status', sa.String(length=50), nullable=True),
        sa.Column('reward_awarded_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['referrer_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['affiliate_id'], ['affiliate_programs.id'], ),
        sa.ForeignKeyConstraint(['referred_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_referrals_referrer', 'referrals', ['referrer_user_id'])
    op.create_index('idx_referrals_affiliate', 'referrals', ['affiliate_id'])
    op.create_index('idx_referrals_referred', 'referrals', ['referred_user_id'])
    op.create_index('idx_referrals_code', 'referrals', ['referral_code'])
    op.create_index('idx_referrals_converted', 'referrals', ['converted'])

    # Create partner_earnings table
    op.create_table(
        'partner_earnings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('affiliate_id', sa.Integer(), nullable=False),
        sa.Column('referral_id', sa.Integer(), nullable=True),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('earning_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('base_amount', sa.Integer(), nullable=True),
        sa.Column('commission_rate', sa.Float(), nullable=True),
        sa.Column('billing_period', sa.String(length=20), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('payout_id', sa.String(length=255), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['affiliate_id'], ['affiliate_programs.id'], ),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_partner_earnings_affiliate', 'partner_earnings', ['affiliate_id'])
    op.create_index('idx_partner_earnings_status', 'partner_earnings', ['status'])

    # Create content_creator_revenues table
    op.create_table(
        'content_creator_revenues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('creator_user_id', sa.Integer(), nullable=False),
        sa.Column('channel_id', sa.Integer(), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('revenue_type', sa.String(length=50), nullable=False),
        sa.Column('total_revenue', sa.Integer(), nullable=False),
        sa.Column('creator_share', sa.Integer(), nullable=False),
        sa.Column('platform_share', sa.Integer(), nullable=False),
        sa.Column('revenue_split_percentage', sa.Float(), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('billing_period', sa.String(length=20), nullable=True),
        sa.Column('payout_status', sa.String(length=50), nullable=True),
        sa.Column('payout_date', sa.DateTime(), nullable=True),
        sa.Column('payout_method', sa.String(length=50), nullable=True),
        sa.Column('payout_reference', sa.String(length=255), nullable=True),
        sa.Column('content_views', sa.Integer(), nullable=True),
        sa.Column('api_calls_attributed', sa.Integer(), nullable=True),
        sa.Column('matches_attributed', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['creator_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_creator_revenue_creator', 'content_creator_revenues', ['creator_user_id'])
    op.create_index('idx_creator_revenue_period', 'content_creator_revenues', ['period_start', 'period_end'])
    op.create_index('idx_creator_revenue_status', 'content_creator_revenues', ['payout_status'])

    # Create marketplace_items table
    op.create_table(
        'marketplace_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('pricing_model', sa.String(length=50), nullable=True),
        sa.Column('marketplace_fee_percentage', sa.Float(), nullable=True),
        sa.Column('file_url', sa.String(length=500), nullable=True),
        sa.Column('file_size_mb', sa.Float(), nullable=True),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('license_type', sa.String(length=100), nullable=True),
        sa.Column('download_count', sa.Integer(), nullable=True),
        sa.Column('purchase_count', sa.Integer(), nullable=True),
        sa.Column('total_revenue', sa.Integer(), nullable=True),
        sa.Column('average_rating', sa.Float(), nullable=True),
        sa.Column('review_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('preview_url', sa.String(length=500), nullable=True),
        sa.Column('demo_available', sa.Boolean(), nullable=True),
        sa.Column('sample_data_url', sa.String(length=500), nullable=True),
        sa.Column('min_plan_tier', sa.String(length=50), nullable=True),
        sa.Column('api_access_required', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['seller_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_marketplace_items_seller', 'marketplace_items', ['seller_user_id'])
    op.create_index('idx_marketplace_items_status', 'marketplace_items', ['status'])
    op.create_index('idx_marketplace_items_type', 'marketplace_items', ['item_type'])

    # Create marketplace_transactions table
    op.create_table(
        'marketplace_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('marketplace_item_id', sa.Integer(), nullable=False),
        sa.Column('buyer_user_id', sa.Integer(), nullable=False),
        sa.Column('seller_user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('marketplace_fee', sa.Integer(), nullable=False),
        sa.Column('seller_payout', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('payment_status', sa.String(length=50), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('seller_payout_status', sa.String(length=50), nullable=True),
        sa.Column('seller_payout_date', sa.DateTime(), nullable=True),
        sa.Column('seller_payout_reference', sa.String(length=255), nullable=True),
        sa.Column('license_key', sa.String(length=255), nullable=True),
        sa.Column('access_granted', sa.Boolean(), nullable=True),
        sa.Column('download_url', sa.String(length=500), nullable=True),
        sa.Column('download_expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['marketplace_item_id'], ['marketplace_items.id'], ),
        sa.ForeignKeyConstraint(['buyer_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['seller_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_key')
    )
    op.create_index('idx_marketplace_transactions_item', 'marketplace_transactions', ['marketplace_item_id'])
    op.create_index('idx_marketplace_transactions_buyer', 'marketplace_transactions', ['buyer_user_id'])
    op.create_index('idx_marketplace_transactions_seller', 'marketplace_transactions', ['seller_user_id'])

    # Create white_label_resellers table
    op.create_table(
        'white_label_resellers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_website', sa.String(length=500), nullable=True),
        sa.Column('contact_name', sa.String(length=255), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=50), nullable=True),
        sa.Column('custom_domain', sa.String(length=255), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('brand_name', sa.String(length=255), nullable=True),
        sa.Column('volume_discount_percentage', sa.Float(), nullable=True),
        sa.Column('markup_percentage', sa.Float(), nullable=True),
        sa.Column('custom_pricing_enabled', sa.Boolean(), nullable=True),
        sa.Column('max_end_users', sa.Integer(), nullable=True),
        sa.Column('max_api_calls_per_month', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('contract_start_date', sa.DateTime(), nullable=True),
        sa.Column('contract_end_date', sa.DateTime(), nullable=True),
        sa.Column('total_end_users', sa.Integer(), nullable=True),
        sa.Column('total_revenue', sa.Integer(), nullable=True),
        sa.Column('total_api_calls', sa.Integer(), nullable=True),
        sa.Column('payment_terms', sa.String(length=100), nullable=True),
        sa.Column('billing_contact_email', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('custom_domain')
    )
    op.create_index('idx_white_label_user', 'white_label_resellers', ['user_id'])
    op.create_index('idx_white_label_domain', 'white_label_resellers', ['custom_domain'])
    op.create_index('idx_white_label_status', 'white_label_resellers', ['status'])

    # Create reward_transactions table
    op.create_table(
        'reward_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('reward_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=False),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('transaction_type', sa.String(length=20), nullable=False),
        sa.Column('balance_before', sa.Integer(), nullable=True),
        sa.Column('balance_after', sa.Integer(), nullable=True),
        sa.Column('referral_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('achievement_id', sa.String(length=100), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('expired', sa.Boolean(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['referral_id'], ['referrals.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reward_transactions_user', 'reward_transactions', ['user_id'])
    op.create_index('idx_reward_transactions_type', 'reward_transactions', ['reward_type'])
    op.create_index('idx_reward_transactions_status', 'reward_transactions', ['status'])

    # Create user_badges table
    op.create_table(
        'user_badges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('badge_id', sa.String(length=100), nullable=False),
        sa.Column('badge_name', sa.String(length=255), nullable=False),
        sa.Column('badge_description', sa.Text(), nullable=True),
        sa.Column('badge_icon_url', sa.String(length=500), nullable=True),
        sa.Column('badge_tier', sa.String(length=50), nullable=True),
        sa.Column('achievement_type', sa.String(length=100), nullable=True),
        sa.Column('achievement_value', sa.Integer(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('earned_at', sa.DateTime(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_badges_user', 'user_badges', ['user_id'])
    op.create_index('idx_user_badges_badge', 'user_badges', ['badge_id'])

    # Create leaderboards table
    op.create_table(
        'leaderboards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('period_type', sa.String(length=50), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('previous_rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('total_referrals', sa.Integer(), nullable=True),
        sa.Column('total_api_calls', sa.Integer(), nullable=True),
        sa.Column('total_revenue', sa.Integer(), nullable=True),
        sa.Column('total_content_views', sa.Integer(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_leaderboards_user', 'leaderboards', ['user_id'])
    op.create_index('idx_leaderboards_category', 'leaderboards', ['category'])
    op.create_index('idx_leaderboards_period', 'leaderboards', ['period_type', 'period_start'])

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('campaign_code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('campaign_type', sa.String(length=50), nullable=False),
        sa.Column('offer_type', sa.String(length=50), nullable=False),
        sa.Column('discount_percentage', sa.Float(), nullable=True),
        sa.Column('discount_amount', sa.Integer(), nullable=True),
        sa.Column('credit_amount', sa.Integer(), nullable=True),
        sa.Column('free_trial_days', sa.Integer(), nullable=True),
        sa.Column('target_audience', sa.String(length=100), nullable=True),
        sa.Column('target_plan_tiers', sa.JSON(), nullable=True),
        sa.Column('target_regions', sa.JSON(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('max_uses_per_user', sa.Integer(), nullable=True),
        sa.Column('current_uses', sa.Integer(), nullable=True),
        sa.Column('total_clicks', sa.Integer(), nullable=True),
        sa.Column('total_conversions', sa.Integer(), nullable=True),
        sa.Column('total_revenue', sa.Integer(), nullable=True),
        sa.Column('conversion_rate', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_code')
    )
    op.create_index('idx_campaigns_code', 'campaigns', ['campaign_code'])
    op.create_index('idx_campaigns_status', 'campaigns', ['status'])
    op.create_index('idx_campaigns_dates', 'campaigns', ['start_date', 'end_date'])

    # Add foreign key from reward_transactions to campaigns (deferred due to table ordering)
    op.create_foreign_key(
        'fk_reward_transactions_campaign_id',
        'reward_transactions',
        'campaigns',
        ['campaign_id'],
        ['id']
    )


def downgrade() -> None:
    # Drop in reverse order
    op.drop_index('idx_campaigns_dates', table_name='campaigns')
    op.drop_index('idx_campaigns_status', table_name='campaigns')
    op.drop_index('idx_campaigns_code', table_name='campaigns')
    op.drop_table('campaigns')

    op.drop_index('idx_leaderboards_period', table_name='leaderboards')
    op.drop_index('idx_leaderboards_category', table_name='leaderboards')
    op.drop_index('idx_leaderboards_user', table_name='leaderboards')
    op.drop_table('leaderboards')

    op.drop_index('idx_user_badges_badge', table_name='user_badges')
    op.drop_index('idx_user_badges_user', table_name='user_badges')
    op.drop_table('user_badges')

    op.drop_index('idx_reward_transactions_status', table_name='reward_transactions')
    op.drop_index('idx_reward_transactions_type', table_name='reward_transactions')
    op.drop_index('idx_reward_transactions_user', table_name='reward_transactions')
    op.drop_table('reward_transactions')

    op.drop_index('idx_white_label_status', table_name='white_label_resellers')
    op.drop_index('idx_white_label_domain', table_name='white_label_resellers')
    op.drop_index('idx_white_label_user', table_name='white_label_resellers')
    op.drop_table('white_label_resellers')

    op.drop_index('idx_marketplace_transactions_seller', table_name='marketplace_transactions')
    op.drop_index('idx_marketplace_transactions_buyer', table_name='marketplace_transactions')
    op.drop_index('idx_marketplace_transactions_item', table_name='marketplace_transactions')
    op.drop_table('marketplace_transactions')

    op.drop_index('idx_marketplace_items_type', table_name='marketplace_items')
    op.drop_index('idx_marketplace_items_status', table_name='marketplace_items')
    op.drop_index('idx_marketplace_items_seller', table_name='marketplace_items')
    op.drop_table('marketplace_items')

    op.drop_index('idx_creator_revenue_status', table_name='content_creator_revenues')
    op.drop_index('idx_creator_revenue_period', table_name='content_creator_revenues')
    op.drop_index('idx_creator_revenue_creator', table_name='content_creator_revenues')
    op.drop_table('content_creator_revenues')

    op.drop_index('idx_partner_earnings_status', table_name='partner_earnings')
    op.drop_index('idx_partner_earnings_affiliate', table_name='partner_earnings')
    op.drop_table('partner_earnings')

    op.drop_index('idx_referrals_converted', table_name='referrals')
    op.drop_index('idx_referrals_code', table_name='referrals')
    op.drop_index('idx_referrals_referred', table_name='referrals')
    op.drop_index('idx_referrals_affiliate', table_name='referrals')
    op.drop_index('idx_referrals_referrer', table_name='referrals')
    op.drop_table('referrals')

    op.drop_index('idx_affiliate_programs_status', table_name='affiliate_programs')
    op.drop_index('idx_affiliate_programs_code', table_name='affiliate_programs')
    op.drop_index('idx_affiliate_programs_user_id', table_name='affiliate_programs')
    op.drop_table('affiliate_programs')
