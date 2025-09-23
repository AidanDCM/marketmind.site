"""merge heads for phase9 governance

Revision ID: a8b7a2b93ab0
Revises: 9f1a2b3c4d5e, 41731d0dfc1a
Create Date: 2025-08-22 17:44:03.264351+00:00

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a8b7a2b93ab0"
down_revision: Union[str, Sequence[str], None] = ("9f1a2b3c4d5e", "41731d0dfc1a")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
