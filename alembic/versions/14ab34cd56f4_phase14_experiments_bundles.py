"""phase14 experiment variants, bundles, cohorts, and attribution extensions

Revision ID: 14ab34cd56f4
Revises: 13ab34cd56f3
Create Date: 2025-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "14ab34cd56f4"
down_revision: Union[str, Sequence[str], None] = "13ab34cd56f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # experiment_variant
    if not insp.has_table("experiment_variant"):
        op.create_table(
            "experiment_variant",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("experiment_id", sa.Integer, sa.ForeignKey("experiment.id"), nullable=False),
            sa.Column("key", sa.String(64), nullable=False),
            sa.Column("name", sa.String(255), nullable=True),
            sa.Column("params", sa.Text, nullable=True),
            sa.Column("allocation_weight", sa.Float, nullable=False, server_default="1.0"),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        )
        op.create_index(
            "ix_experiment_variant_experiment_id", "experiment_variant", ["experiment_id"]
        )
        op.create_index("ix_experiment_variant_key", "experiment_variant", ["key"])
        op.create_index("ix_experiment_variant_status", "experiment_variant", ["status"])

    # bundle_trial
    if not insp.has_table("bundle_trial"):
        op.create_table(
            "bundle_trial",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("experiment_id", sa.Integer, sa.ForeignKey("experiment.id"), nullable=True),
            sa.Column("org_id", sa.String(64), nullable=True),
            sa.Column("brain_id", sa.String(64), nullable=True),
            sa.Column("bundle_ref", sa.String(128), nullable=False),
            sa.Column("components", sa.Text, nullable=True),
            sa.Column("channel", sa.String(64), nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
            sa.Column("guardrail_flags", sa.Text, nullable=True),
            sa.Column("published_at", sa.DateTime, nullable=True),
            sa.Column("retired_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_bundle_trial_experiment_id", "bundle_trial", ["experiment_id"])
        op.create_index("ix_bundle_trial_org_id", "bundle_trial", ["org_id"])
        op.create_index("ix_bundle_trial_brain_id", "bundle_trial", ["brain_id"])
        op.create_index("ix_bundle_trial_bundle_ref", "bundle_trial", ["bundle_ref"])
        op.create_index("ix_bundle_trial_channel", "bundle_trial", ["channel"])
        op.create_index("ix_bundle_trial_status", "bundle_trial", ["status"])

    # bundle_result
    if not insp.has_table("bundle_result"):
        op.create_table(
            "bundle_result",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column(
                "bundle_trial_id", sa.Integer, sa.ForeignKey("bundle_trial.id"), nullable=False
            ),
            sa.Column("metric", sa.String(64), nullable=False),
            sa.Column("value", sa.Float, nullable=False, server_default="0"),
            sa.Column("sample_size", sa.Integer, nullable=True),
            sa.Column("observed_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_bundle_result_bundle_trial_id", "bundle_result", ["bundle_trial_id"])
        op.create_index("ix_bundle_result_metric", "bundle_result", ["metric"])

    # customer_cohort
    if not insp.has_table("customer_cohort"):
        op.create_table(
            "customer_cohort",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("org_id", sa.String(64), nullable=True),
            sa.Column("brain_id", sa.String(64), nullable=True),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("rule", sa.Text, nullable=True),
            sa.Column("size_estimate", sa.Integer, nullable=True),
            sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        )
        op.create_index("ix_customer_cohort_org_id", "customer_cohort", ["org_id"])
        op.create_index("ix_customer_cohort_brain_id", "customer_cohort", ["brain_id"])
        op.create_index("ix_customer_cohort_name", "customer_cohort", ["name"])
        op.create_index("ix_customer_cohort_status", "customer_cohort", ["status"])

    # attribution_event new columns (SQLite-safe) with idempotency
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    aev_cols = {c["name"] for c in sa.inspect(bind).get_columns("attribution_event")}
    existing_indexes = {ix["name"] for ix in sa.inspect(bind).get_indexes("attribution_event")}

    if is_sqlite:
        # SQLite cannot ALTER TABLE to add FK constraints; add plain columns via batch
        with op.batch_alter_table("attribution_event") as batch_op:
            if "experiment_id" not in aev_cols:
                batch_op.add_column(sa.Column("experiment_id", sa.Integer, nullable=True))
            if "variant_key" not in aev_cols:
                batch_op.add_column(sa.Column("variant_key", sa.String(64), nullable=True))
            if "bundle_trial_id" not in aev_cols:
                batch_op.add_column(sa.Column("bundle_trial_id", sa.Integer, nullable=True))
    else:
        if "experiment_id" not in aev_cols:
            op.add_column(
                "attribution_event",
                sa.Column(
                    "experiment_id", sa.Integer, sa.ForeignKey("experiment.id"), nullable=True
                ),
            )
        if "variant_key" not in aev_cols:
            op.add_column(
                "attribution_event", sa.Column("variant_key", sa.String(64), nullable=True)
            )
        if "bundle_trial_id" not in aev_cols:
            op.add_column(
                "attribution_event",
                sa.Column(
                    "bundle_trial_id", sa.Integer, sa.ForeignKey("bundle_trial.id"), nullable=True
                ),
            )

    if (
        "ix_attribution_event_experiment_id" not in existing_indexes
        and "experiment_id" in aev_cols
        or "experiment_id" in {"experiment_id"}
    ):
        # Create index if not exists (SQLAlchemy doesn't support IF NOT EXISTS across all backends)
        try:
            op.create_index(
                "ix_attribution_event_experiment_id", "attribution_event", ["experiment_id"]
            )
        except Exception:
            pass
    if "ix_attribution_event_variant_key" not in existing_indexes and (
        "variant_key" in aev_cols or True
    ):
        try:
            op.create_index(
                "ix_attribution_event_variant_key", "attribution_event", ["variant_key"]
            )
        except Exception:
            pass
    if "ix_attribution_event_bundle_trial_id" not in existing_indexes and (
        "bundle_trial_id" in aev_cols or True
    ):
        try:
            op.create_index(
                "ix_attribution_event_bundle_trial_id", "attribution_event", ["bundle_trial_id"]
            )
        except Exception:
            pass


def downgrade() -> None:
    # attribution_event columns (SQLite-safe) with guards
    bind = op.get_bind()
    aev_cols = {c["name"] for c in sa.inspect(bind).get_columns("attribution_event")}
    existing_indexes = {ix["name"] for ix in sa.inspect(bind).get_indexes("attribution_event")}

    if "ix_attribution_event_bundle_trial_id" in existing_indexes:
        op.drop_index("ix_attribution_event_bundle_trial_id", table_name="attribution_event")
    if "ix_attribution_event_variant_key" in existing_indexes:
        op.drop_index("ix_attribution_event_variant_key", table_name="attribution_event")
    if "ix_attribution_event_experiment_id" in existing_indexes:
        op.drop_index("ix_attribution_event_experiment_id", table_name="attribution_event")

    is_sqlite = bind.dialect.name == "sqlite"
    if is_sqlite:
        with op.batch_alter_table("attribution_event") as batch_op:
            if "bundle_trial_id" in aev_cols:
                batch_op.drop_column("bundle_trial_id")
            if "variant_key" in aev_cols:
                batch_op.drop_column("variant_key")
            if "experiment_id" in aev_cols:
                batch_op.drop_column("experiment_id")
    else:
        if "bundle_trial_id" in aev_cols:
            op.drop_column("attribution_event", "bundle_trial_id")
        if "variant_key" in aev_cols:
            op.drop_column("attribution_event", "variant_key")
        if "experiment_id" in aev_cols:
            op.drop_column("attribution_event", "experiment_id")

    # customer_cohort
    op.drop_index("ix_customer_cohort_status", table_name="customer_cohort")
    op.drop_index("ix_customer_cohort_name", table_name="customer_cohort")
    op.drop_index("ix_customer_cohort_brain_id", table_name="customer_cohort")
    op.drop_index("ix_customer_cohort_org_id", table_name="customer_cohort")
    op.drop_table("customer_cohort")

    # bundle_result
    op.drop_index("ix_bundle_result_metric", table_name="bundle_result")
    op.drop_index("ix_bundle_result_bundle_trial_id", table_name="bundle_result")
    op.drop_table("bundle_result")

    # bundle_trial
    op.drop_index("ix_bundle_trial_status", table_name="bundle_trial")
    op.drop_index("ix_bundle_trial_channel", table_name="bundle_trial")
    op.drop_index("ix_bundle_trial_bundle_ref", table_name="bundle_trial")
    op.drop_index("ix_bundle_trial_brain_id", table_name="bundle_trial")
    op.drop_index("ix_bundle_trial_org_id", table_name="bundle_trial")
    op.drop_index("ix_bundle_trial_experiment_id", table_name="bundle_trial")
    op.drop_table("bundle_trial")

    # experiment_variant
    op.drop_index("ix_experiment_variant_status", table_name="experiment_variant")
    op.drop_index("ix_experiment_variant_key", table_name="experiment_variant")
    op.drop_index("ix_experiment_variant_experiment_id", table_name="experiment_variant")
    op.drop_table("experiment_variant")
