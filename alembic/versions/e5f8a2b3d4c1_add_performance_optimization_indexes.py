"""add_performance_optimization_indexes

Revision ID: e5f8a2b3d4c1
Revises: c8e9d4a1f2b3
Create Date: 2025-10-28 17:10:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f8a2b3d4c1"
down_revision: Union[str, Sequence[str], None] = "c8e9d4a1f2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add performance optimization indexes."""
    
    # Job queue queries - partial index for active jobs
    op.create_index(
        "idx_jobs_status_created",
        "processing_jobs",
        ["status", "created_at"],
        unique=False,
        postgresql_where="status IN ('pending', 'running')",
    )
    
    # Video lookup queries - composite index for channel and date
    op.create_index(
        "idx_videos_channel_date",
        "videos",
        ["channel_id", "upload_date"],
        unique=False,
    )
    
    # Channel queries - partial index for active channels
    op.create_index(
        "idx_channels_active",
        "channels",
        ["is_active", "last_processed"],
        unique=False,
        postgresql_where="is_active = true",
    )
    
    # Partial index for unprocessed videos
    op.create_index(
        "idx_videos_unprocessed",
        "videos",
        ["created_at"],
        unique=False,
        postgresql_where="processed = false",
    )
    
    # Partial index for failed jobs
    op.create_index(
        "idx_jobs_failed",
        "processing_jobs",
        ["job_type", "created_at"],
        unique=False,
        postgresql_where="status = 'failed'",
    )


def downgrade() -> None:
    """Downgrade schema - remove performance optimization indexes."""
    op.drop_index("idx_jobs_failed", table_name="processing_jobs")
    op.drop_index("idx_videos_unprocessed", table_name="videos")
    op.drop_index("idx_channels_active", table_name="channels")
    op.drop_index("idx_videos_channel_date", table_name="videos")
    op.drop_index("idx_jobs_status_created", table_name="processing_jobs")
