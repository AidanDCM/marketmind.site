"""
Add ingest_checkpoints table for Phase 5 ingestion checkpoints

Revision ID: f1e2d3c4
Revises: e7f6a5d4c3b2
Create Date: 2025-08-19 23:35:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "f1e2d3c4"
down_revision = "e7f6a5d4c3b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_checkpoints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(length=64), nullable=True),
        sa.Column("brain_id", sa.String(length=64), nullable=True),
        sa.Column("pipeline", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=True),
        sa.Column("value", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "org_id",
            "brain_id",
            "pipeline",
            "source",
            "key",
            name="uq_ingest_ckpt_scope",
        ),
    )
    op.create_index("ix_ingest_ckpts_org_id", "ingest_checkpoints", ["org_id"], unique=False)
    op.create_index("ix_ingest_ckpts_brain_id", "ingest_checkpoints", ["brain_id"], unique=False)
    op.create_index("ix_ingest_ckpts_pipeline", "ingest_checkpoints", ["pipeline"], unique=False)
    op.create_index("ix_ingest_ckpts_source", "ingest_checkpoints", ["source"], unique=False)
    op.create_index("ix_ingest_ckpts_key", "ingest_checkpoints", ["key"], unique=False)
    op.create_index(
        "ix_ingest_ckpts_updated_at", "ingest_checkpoints", ["updated_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_ingest_ckpts_updated_at", table_name="ingest_checkpoints")
    op.drop_index("ix_ingest_ckpts_key", table_name="ingest_checkpoints")
    op.drop_index("ix_ingest_ckpts_source", table_name="ingest_checkpoints")
    op.drop_index("ix_ingest_ckpts_pipeline", table_name="ingest_checkpoints")
    op.drop_index("ix_ingest_ckpts_brain_id", table_name="ingest_checkpoints")
    op.drop_index("ix_ingest_ckpts_org_id", table_name="ingest_checkpoints")
    op.drop_table("ingest_checkpoints")
