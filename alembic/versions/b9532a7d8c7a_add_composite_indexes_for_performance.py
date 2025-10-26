"""add_composite_indexes_for_performance

Revision ID: b9532a7d8c7a
Revises: ce1ffb204f19
Create Date: 2025-10-26 02:33:52.488676

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9532a7d8c7a"
down_revision: Union[str, Sequence[str], None] = "ce1ffb204f19"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add composite indexes for performance."""
    # Composite indexes for audio_fingerprints table
    op.create_index(
        "idx_fingerprints_video_time",
        "audio_fingerprints",
        ["video_id", "start_time"],
        unique=False,
    )
    op.create_index(
        "idx_fingerprints_hash_video",
        "audio_fingerprints",
        ["fingerprint_hash", "video_id"],
        unique=False,
    )

    # Composite indexes for match_results table
    op.create_index(
        "idx_match_results_query_fp",
        "match_results",
        ["query_fingerprint_id", "similarity_score"],
        unique=False,
    )
    op.create_index(
        "idx_match_results_matched_fp",
        "match_results",
        ["matched_fingerprint_id", "similarity_score"],
        unique=False,
    )

    # Composite indexes for processing_jobs table
    op.create_index(
        "idx_processing_jobs_type_status",
        "processing_jobs",
        ["job_type", "status"],
        unique=False,
    )
    op.create_index(
        "idx_processing_jobs_target",
        "processing_jobs",
        ["target_id", "job_type", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema - remove composite indexes."""
    # Drop composite indexes in reverse order
    op.drop_index("idx_processing_jobs_target", table_name="processing_jobs")
    op.drop_index("idx_processing_jobs_type_status", table_name="processing_jobs")
    op.drop_index("idx_match_results_matched_fp", table_name="match_results")
    op.drop_index("idx_match_results_query_fp", table_name="match_results")
    op.drop_index("idx_fingerprints_hash_video", table_name="audio_fingerprints")
    op.drop_index("idx_fingerprints_video_time", table_name="audio_fingerprints")
