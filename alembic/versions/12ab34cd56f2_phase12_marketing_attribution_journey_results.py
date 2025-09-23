"""phase12 marketing attribution, journey, experiment results

Revision ID: 12ab34cd56f2
Revises: 12ab34cd56f1
Create Date: 2025-08-22

Creates Phase 12 tables:
- experiment_result
- customer_journey
- attribution_event
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12ab34cd56f2"
down_revision: Union[str, Sequence[str], None] = "12ab34cd56f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experiment_result",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("experiment_id", sa.Integer, sa.ForeignKey("experiment.id"), nullable=False),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("variant", sa.String(32), nullable=False),
        sa.Column("metric", sa.String(64), nullable=False),
        sa.Column("value", sa.Float, nullable=False, server_default="0"),
        sa.Column("sample_size", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("observed_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_experiment_result_experiment_id", "experiment_result", ["experiment_id"])
    op.create_index("ix_experiment_result_org_id", "experiment_result", ["org_id"])
    op.create_index("ix_experiment_result_brain_id", "experiment_result", ["brain_id"])
    op.create_index("ix_experiment_result_metric", "experiment_result", ["metric"])

    op.create_table(
        "customer_journey",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("customer_ref", sa.String(128), nullable=True),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("medium", sa.String(64), nullable=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaign.id"), nullable=True),
        sa.Column("meta", sa.Text, nullable=True),
    )
    op.create_index("ix_customer_journey_org_id", "customer_journey", ["org_id"])
    op.create_index("ix_customer_journey_brain_id", "customer_journey", ["brain_id"])
    op.create_index("ix_customer_journey_customer_ref", "customer_journey", ["customer_ref"])
    op.create_index("ix_customer_journey_stage", "customer_journey", ["stage"])
    op.create_index("ix_customer_journey_campaign_id", "customer_journey", ["campaign_id"])

    op.create_table(
        "attribution_event",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaign.id"), nullable=True),
        sa.Column("source", sa.String(64), nullable=True),
        sa.Column("medium", sa.String(64), nullable=True),
        sa.Column("channel", sa.String(64), nullable=True),
        sa.Column("event", sa.String(64), nullable=False),
        sa.Column("value", sa.Float, nullable=True),
        sa.Column("currency", sa.String(8), nullable=True),
        sa.Column("customer_ref", sa.String(128), nullable=True),
        sa.Column("meta", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_attribution_event_org_id", "attribution_event", ["org_id"])
    op.create_index("ix_attribution_event_brain_id", "attribution_event", ["brain_id"])
    op.create_index("ix_attribution_event_campaign_id", "attribution_event", ["campaign_id"])
    op.create_index("ix_attribution_event_source", "attribution_event", ["source"])
    op.create_index("ix_attribution_event_medium", "attribution_event", ["medium"])
    op.create_index("ix_attribution_event_channel", "attribution_event", ["channel"])
    op.create_index("ix_attribution_event_event", "attribution_event", ["event"])
    op.create_index("ix_attribution_event_customer_ref", "attribution_event", ["customer_ref"])
    op.create_index("ix_attribution_event_occurred_at", "attribution_event", ["occurred_at"])


def downgrade() -> None:
    op.drop_index("ix_attribution_event_occurred_at", table_name="attribution_event")
    op.drop_index("ix_attribution_event_customer_ref", table_name="attribution_event")
    op.drop_index("ix_attribution_event_event", table_name="attribution_event")
    op.drop_index("ix_attribution_event_channel", table_name="attribution_event")
    op.drop_index("ix_attribution_event_medium", table_name="attribution_event")
    op.drop_index("ix_attribution_event_source", table_name="attribution_event")
    op.drop_index("ix_attribution_event_campaign_id", table_name="attribution_event")
    op.drop_index("ix_attribution_event_brain_id", table_name="attribution_event")
    op.drop_index("ix_attribution_event_org_id", table_name="attribution_event")
    op.drop_table("attribution_event")

    op.drop_index("ix_customer_journey_campaign_id", table_name="customer_journey")
    op.drop_index("ix_customer_journey_stage", table_name="customer_journey")
    op.drop_index("ix_customer_journey_customer_ref", table_name="customer_journey")
    op.drop_index("ix_customer_journey_brain_id", table_name="customer_journey")
    op.drop_index("ix_customer_journey_org_id", table_name="customer_journey")
    op.drop_table("customer_journey")

    op.drop_index("ix_experiment_result_metric", table_name="experiment_result")
    op.drop_index("ix_experiment_result_brain_id", table_name="experiment_result")
    op.drop_index("ix_experiment_result_org_id", table_name="experiment_result")
    op.drop_index("ix_experiment_result_experiment_id", table_name="experiment_result")
    op.drop_table("experiment_result")
