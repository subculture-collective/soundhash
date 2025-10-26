"""add_fingerprint_parameters_for_caching

Revision ID: c8e9d4a1f2b3
Revises: b9532a7d8c7a
Create Date: 2025-10-26 14:24:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8e9d4a1f2b3"
down_revision: str | Sequence[str] | None = "b9532a7d8c7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add fingerprint extraction parameters for cache invalidation."""
    # Add n_fft column with NOT NULL and default value 2048
    # PostgreSQL 11+ optimizes adding NOT NULL columns with DEFAULT as a metadata-only
    # operation, making this instant even on large tables (no table scan/rewrite needed).
    # This eliminates the need for UPDATE statements.
    op.add_column(
        "audio_fingerprints",
        sa.Column("n_fft", sa.Integer(), nullable=False, server_default="2048"),
    )

    # Add hop_length column with NOT NULL and default value 512
    op.add_column(
        "audio_fingerprints",
        sa.Column("hop_length", sa.Integer(), nullable=False, server_default="512"),
    )


def downgrade() -> None:
    """Downgrade schema - remove fingerprint extraction parameters."""
    op.drop_column("audio_fingerprints", "hop_length")
    op.drop_column("audio_fingerprints", "n_fft")
