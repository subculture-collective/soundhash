"""add onboarding tables

Revision ID: d4e8a9b2c1f5
Revises: ce3adb6ef385
Create Date: 2025-10-30 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd4e8a9b2c1f5'
down_revision = 'ce3adb6ef385'
branch_labels = None
depends_on = None


def upgrade():
    # Create onboarding_progress table
    op.create_table('onboarding_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('use_case', sa.String(length=50), nullable=True),
        sa.Column('welcome_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('use_case_selected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('api_key_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('first_upload_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('dashboard_explored', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('integration_started', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tour_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tour_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tour_last_step', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('sample_data_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('custom_data', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_onboarding_progress_user_id', 'onboarding_progress', ['user_id'])
    op.create_index('idx_onboarding_progress_is_completed', 'onboarding_progress', ['is_completed'])
    op.create_index('idx_onboarding_progress_use_case', 'onboarding_progress', ['use_case'])

    # Create tutorial_progress table
    op.create_table('tutorial_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tutorial_id', sa.String(length=100), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('progress_percent', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_step', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('last_viewed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_tutorial_progress_user_id', 'tutorial_progress', ['user_id'])
    op.create_index('idx_tutorial_progress_tutorial_id', 'tutorial_progress', ['tutorial_id'])
    op.create_index('idx_tutorial_progress_user_tutorial', 'tutorial_progress', ['user_id', 'tutorial_id'])

    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('show_tooltips', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_contextual_help', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('auto_start_tours', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('show_onboarding_tips', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('daily_tips_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('theme', sa.String(length=20), nullable=True, server_default='system'),
        sa.Column('language', sa.String(length=10), nullable=True, server_default='en'),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('beta_features_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('preferences_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])


def downgrade():
    op.drop_index('idx_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
    
    op.drop_index('idx_tutorial_progress_user_tutorial', table_name='tutorial_progress')
    op.drop_index('idx_tutorial_progress_tutorial_id', table_name='tutorial_progress')
    op.drop_index('idx_tutorial_progress_user_id', table_name='tutorial_progress')
    op.drop_table('tutorial_progress')
    
    op.drop_index('idx_onboarding_progress_use_case', table_name='onboarding_progress')
    op.drop_index('idx_onboarding_progress_is_completed', table_name='onboarding_progress')
    op.drop_index('idx_onboarding_progress_user_id', table_name='onboarding_progress')
    op.drop_table('onboarding_progress')
