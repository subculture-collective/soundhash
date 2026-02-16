"""merge_three_heads

Revision ID: f78a03bf92c3
Revises: d4e8a9b2c1f5, ef282c9b1cb3, m1a2b3c4d5e6
Create Date: 2026-02-16 04:50:34.292213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f78a03bf92c3'
down_revision: Union[str, Sequence[str], None] = ('d4e8a9b2c1f5', 'ef282c9b1cb3', 'm1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
