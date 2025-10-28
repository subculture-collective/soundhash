"""merge_performance_and_user_api_heads

Revision ID: e0ae37366ae4
Revises: d4a7e3b9c2f1, e5f8a2b3d4c1
Create Date: 2025-10-28 17:21:22.441102

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e0ae37366ae4"
down_revision: Union[str, Sequence[str], None] = ("d4a7e3b9c2f1", "e5f8a2b3d4c1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
