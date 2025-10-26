"""add_fingerprint_parameters_for_caching

Revision ID: c8e9d4a1f2b3
Revises: b9532a7d8c7a
Create Date: 2025-10-26 14:24:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8e9d4a1f2b3"
down_revision: Union[str, Sequence[str], None] = "b9532a7d8c7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add fingerprint extraction parameters for cache invalidation."""
    # Add n_fft column with default value 2048
    op.add_column(
        "audio_fingerprints",
        sa.Column("n_fft", sa.Integer(), nullable=True, server_default="2048")
    )
    
    # Add hop_length column with default value 512
    op.add_column(
        "audio_fingerprints",
        sa.Column("hop_length", sa.Integer(), nullable=True, server_default="512")
    )
    
    # Update existing rows to have the default values (in case server_default doesn't apply)
    op.execute("UPDATE audio_fingerprints SET n_fft = 2048 WHERE n_fft IS NULL")
    op.execute("UPDATE audio_fingerprints SET hop_length = 512 WHERE hop_length IS NULL")


def downgrade() -> None:
    """Downgrade schema - remove fingerprint extraction parameters."""
    op.drop_column("audio_fingerprints", "hop_length")
    op.drop_column("audio_fingerprints", "n_fft")
