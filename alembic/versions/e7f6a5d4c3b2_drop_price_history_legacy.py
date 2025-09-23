"""drop legacy listing-based price_history table if present

Revision ID: e7f6a5d4c3b2
Revises: d6e5c4b3a2c1
Create Date: 2025-08-18 15:46:00.000000

"""

from __future__ import annotations

from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision = "e7f6a5d4c3b2"
down_revision = "d6e5c4b3a2c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    # Only drop legacy table if it exists and the new product-based table is present
    if insp.has_table("price_history_legacy") and insp.has_table("price_history"):
        op.drop_table("price_history_legacy")


def downgrade() -> None:
    # No-op: we won't recreate legacy schema automatically
    pass
