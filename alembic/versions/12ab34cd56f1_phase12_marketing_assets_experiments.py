"""phase12 marketing assets and experiments tables

Revision ID: 12ab34cd56f1
Revises: 12ab34cd56ef
Create Date: 2025-08-22

Creates Phase 12 tables:
- campaign_asset
- experiment
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12ab34cd56f1"
down_revision: Union[str, Sequence[str], None] = "12ab34cd56ef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign_asset",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("data", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
    )
    op.create_index("ix_campaign_asset_campaign_id", "campaign_asset", ["campaign_id"])
    op.create_index("ix_campaign_asset_org_id", "campaign_asset", ["org_id"])
    op.create_index("ix_campaign_asset_brain_id", "campaign_asset", ["brain_id"])
    op.create_index("ix_campaign_asset_status", "campaign_asset", ["status"])

    op.create_table(
        "experiment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaign.id"), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False, server_default="ab"),
        sa.Column("hypothesis", sa.Text, nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("start_at", sa.DateTime, nullable=True),
        sa.Column("end_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_experiment_campaign_id", "experiment", ["campaign_id"])
    op.create_index("ix_experiment_org_id", "experiment", ["org_id"])
    op.create_index("ix_experiment_brain_id", "experiment", ["brain_id"])
    op.create_index("ix_experiment_kind", "experiment", ["kind"])
    op.create_index("ix_experiment_status", "experiment", ["status"])


def downgrade() -> None:
    op.drop_index("ix_experiment_status", table_name="experiment")
    op.drop_index("ix_experiment_kind", table_name="experiment")
    op.drop_index("ix_experiment_brain_id", table_name="experiment")
    op.drop_index("ix_experiment_org_id", table_name="experiment")
    op.drop_index("ix_experiment_campaign_id", table_name="experiment")
    op.drop_table("experiment")

    op.drop_index("ix_campaign_asset_status", table_name="campaign_asset")
    op.drop_index("ix_campaign_asset_brain_id", table_name="campaign_asset")
    op.drop_index("ix_campaign_asset_org_id", table_name="campaign_asset")
    op.drop_index("ix_campaign_asset_campaign_id", table_name="campaign_asset")
    op.drop_table("campaign_asset")
