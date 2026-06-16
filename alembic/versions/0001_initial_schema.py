"""Initial schema — approvals, experiments, experiment_snapshots, events.

Revision ID: 0001
Revises:
Create Date: 2026-06-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "approvals",
        sa.Column("approval_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("expected_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("rollback_plan", sa.Text(), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.Column("approver_note", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("approval_id"),
    )
    op.create_table(
        "experiments",
        sa.Column("experiment_id", sa.String(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("break_even_cac", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.Column("started_at", sa.String(), nullable=False),
        sa.Column("ended_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("experiment_id"),
    )
    op.create_table(
        "experiment_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("experiment_id", sa.String(), nullable=False),
        sa.Column("snapshot_date", sa.String(), nullable=False),
        sa.Column("qualified_visits", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orders", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_ad_spend", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("total_revenue", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("refund_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actual_shipping_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("planned_shipping_cost", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("add_to_cart_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "consecutive_losing_periods", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("budget_cap", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("events")
    op.drop_table("experiment_snapshots")
    op.drop_table("experiments")
    op.drop_table("approvals")
