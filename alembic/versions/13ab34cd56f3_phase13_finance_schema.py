"""phase13 finance schema

Revision ID: 13ab34cd56f3
Revises: 12ab34cd56f2
Create Date: 2025-08-22
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "13ab34cd56f3"
down_revision = "12ab34cd56f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "finance_chart_of_account",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("code", sa.String(), index=True),
        sa.Column("name", sa.String()),
        sa.Column("type", sa.String(), index=True),
        sa.Column("parent_code", sa.String()),
        sa.Column("currency", sa.String()),
    )
    op.create_table(
        "finance_ledger_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("ts", sa.String(), index=True),
        sa.Column("source", sa.String(), index=True),
        sa.Column("external_ref", sa.String(), index=True),
        sa.Column("memo", sa.String()),
        sa.Column("posted", sa.Boolean(), server_default=sa.text("0"), nullable=False),
    )
    op.create_table(
        "finance_ledger_entry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("entry_batch_id", sa.Integer(), index=True),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("account_id", sa.Integer(), index=True),
        sa.Column("ts", sa.String(), index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String()),
        sa.Column("debit", sa.Boolean(), nullable=False),
        sa.Column("ref_type", sa.String(), index=True),
        sa.Column("ref_id", sa.String(), index=True),
        sa.Column("memo", sa.String()),
    )
    op.create_table(
        "finance_supplier_invoice",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("supplier_id", sa.Integer(), index=True),
        sa.Column("invoice_no", sa.String(), index=True),
        sa.Column("invoice_date", sa.String(), index=True),
        sa.Column("due_date", sa.String(), index=True),
        sa.Column("currency", sa.String()),
        sa.Column("subtotal", sa.Float(), server_default="0"),
        sa.Column("tax", sa.Float(), server_default="0"),
        sa.Column("total", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(), server_default="open"),
    )
    op.create_table(
        "finance_payment_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("channel", sa.String(), index=True),
        sa.Column("event_type", sa.String(), index=True),
        sa.Column("event_ts", sa.String(), index=True),
        sa.Column("currency", sa.String()),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("external_id", sa.String(), index=True),
        sa.Column("raw", sa.Text()),
    )
    op.create_table(
        "finance_recon_task",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("scope", sa.String(), index=True),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("started_at", sa.String(), index=True),
        sa.Column("finished_at", sa.String(), index=True),
        sa.Column("stats", sa.Text()),
    )
    op.create_table(
        "finance_cashflow_forecast",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("period_start", sa.String(), index=True),
        sa.Column("period_end", sa.String(), index=True),
        sa.Column("inflow", sa.Float(), server_default="0"),
        sa.Column("outflow", sa.Float(), server_default="0"),
        sa.Column("net", sa.Float(), server_default="0"),
        sa.Column("assumptions", sa.Text()),
    )
    op.create_table(
        "finance_payable",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("org_id", sa.String(), index=True),
        sa.Column("supplier_id", sa.Integer(), index=True),
        sa.Column("invoice_id", sa.Integer(), index=True),
        sa.Column("due_date", sa.String(), index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String()),
        sa.Column("status", sa.String(), server_default="open"),
    )


def downgrade() -> None:
    op.drop_table("finance_payable")
    op.drop_table("finance_cashflow_forecast")
    op.drop_table("finance_recon_task")
    op.drop_table("finance_payment_event")
    op.drop_table("finance_supplier_invoice")
    op.drop_table("finance_ledger_entry")
    op.drop_table("finance_ledger_batch")
    op.drop_table("finance_chart_of_account")
