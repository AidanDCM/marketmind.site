"""ensure product-based price_history base table exists

Revision ID: d6e5c4b3a2c1
Revises: c1a2b3c4d5e6
Create Date: 2025-08-18 15:40:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision = "d6e5c4b3a2c1"
down_revision = "c1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if not insp.has_table("price_history"):
        op.create_table(
            "price_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column(
                "product_id",
                sa.Integer(),
                sa.ForeignKey("products.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("channel", sa.String(length=32), nullable=False),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("source", sa.String(length=64), nullable=False),
            sa.Column(
                "recorded_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
            ),
        )
        # Use a unique index name to avoid collisions with partitioned tables' indexes in SQLite
        existing_index_names = set()
        try:
            existing_index_names = {idx["name"] for idx in insp.get_indexes("price_history")}
        except Exception:
            existing_index_names = set()
        index_name = "ix_price_history_recorded_at_main"
        if index_name not in existing_index_names:
            with op.batch_alter_table("price_history", schema=None) as batch_op:
                batch_op.create_index(index_name, ["recorded_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("price_history"):
        op.drop_table("price_history")
