"""align price_history to product-based schema

Revision ID: c1a2b3c4d5e6
Revises: afc38cf36a3d
Create Date: 2025-08-18 15:12:00.000000

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

# revision identifiers, used by Alembic.
revision = "c1a2b3c4d5e6"
down_revision = "afc38cf36a3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # If a legacy listing-based price_history exists, rename it out of the way
    if insp.has_table("price_history"):
        cols = {c["name"] for c in insp.get_columns("price_history")}
        if "listing_id" in cols or "org_id" in cols:
            # Avoid clobbering an existing legacy rename
            if not insp.has_table("price_history_legacy"):
                op.rename_table("price_history", "price_history_legacy")

    # Create the product-based price_history if not present
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
        with op.batch_alter_table("price_history", schema=None) as batch_op:
            batch_op.create_index(
                batch_op.f("ix_price_history_recorded_at"), ["recorded_at"], unique=False
            )


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    # Drop product-based table if present
    if insp.has_table("price_history"):
        cols = {c["name"] for c in insp.get_columns("price_history")}
        if "product_id" in cols and "channel" in cols and "price" in cols:
            op.drop_table("price_history")

    # Restore legacy if it exists
    if insp.has_table("price_history_legacy") and not insp.has_table("price_history"):
        op.rename_table("price_history_legacy", "price_history")
