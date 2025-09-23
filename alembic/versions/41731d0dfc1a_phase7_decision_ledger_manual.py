"""phase7 decision ledger manual

Revision ID: 41731d0dfc1a
Revises: f1e2d3c4
Create Date: 2025-08-20 06:25:22.512316+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "41731d0dfc1a"
down_revision: Union[str, Sequence[str], None] = "f1e2d3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create decision_log table
    op.create_table(
        "decision_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brain", sa.String(length=32), nullable=False),
        sa.Column("decision_id", sa.String(length=64), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.String(length=64), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("decision", sa.JSON(), nullable=True),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Indexes for decision_log
    op.create_index("ix_decision_log_brain", "decision_log", ["brain"], unique=False)
    op.create_index("ix_decision_log_decision_id", "decision_log", ["decision_id"], unique=False)
    op.create_index("ix_decision_log_product_id", "decision_log", ["product_id"], unique=False)
    op.create_index("ix_decision_log_order_id", "decision_log", ["order_id"], unique=False)
    op.create_index("ix_decision_log_created_at", "decision_log", ["created_at"], unique=False)

    # Create kpi_events table
    op.create_table(
        "kpi_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("brain", sa.String(length=32), nullable=False),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Indexes for kpi_events
    op.create_index("ix_kpi_events_brain", "kpi_events", ["brain"], unique=False)
    op.create_index("ix_kpi_events_metric", "kpi_events", ["metric"], unique=False)
    op.create_index("ix_kpi_events_created_at", "kpi_events", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes then tables (SQLite is lenient, but explicit is better)
    op.drop_index("ix_kpi_events_created_at", table_name="kpi_events")
    op.drop_index("ix_kpi_events_metric", table_name="kpi_events")
    op.drop_index("ix_kpi_events_brain", table_name="kpi_events")
    op.drop_table("kpi_events")

    op.drop_index("ix_decision_log_created_at", table_name="decision_log")
    op.drop_index("ix_decision_log_order_id", table_name="decision_log")
    op.drop_index("ix_decision_log_product_id", table_name="decision_log")
    op.drop_index("ix_decision_log_decision_id", table_name="decision_log")
    op.drop_index("ix_decision_log_brain", table_name="decision_log")
    op.drop_table("decision_log")
