"""phase15 learning models: feature snapshots, model versions, metrics, drift, benchmark, rollout

Revision ID: 15ab34cd56f5
Revises: 14ab34cd56f4
Create Date: 2025-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15ab34cd56f5"
down_revision: Union[str, Sequence[str], None] = "14ab34cd56f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    # feature_snapshot
    if not insp.has_table("feature_snapshot"):
        op.create_table(
            "feature_snapshot",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("org_id", sa.String(64), nullable=True),
            sa.Column("brain_id", sa.String(64), nullable=True),
            sa.Column("feature_key", sa.String(128), nullable=False),
            sa.Column("value_json", sa.Text, nullable=True),
            sa.Column("observed_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_feature_snapshot_org_id", "feature_snapshot", ["org_id"])
        op.create_index("ix_feature_snapshot_brain_id", "feature_snapshot", ["brain_id"])
        op.create_index("ix_feature_snapshot_feature_key", "feature_snapshot", ["feature_key"])
        op.create_index("ix_feature_snapshot_observed_at", "feature_snapshot", ["observed_at"])

    # model_version
    if not insp.has_table("model_version"):
        op.create_table(
            "model_version",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("org_id", sa.String(64), nullable=True),
            sa.Column("brain_id", sa.String(64), nullable=False),
            sa.Column("version", sa.String(64), nullable=False),
            sa.Column("status", sa.String(32), nullable=False, server_default="trained"),
            sa.Column("dataset_range", sa.String(64), nullable=True),
            sa.Column("trained_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_model_version_org_id", "model_version", ["org_id"])
        op.create_index("ix_model_version_brain_id", "model_version", ["brain_id"])
        op.create_index("ix_model_version_version", "model_version", ["version"])
        op.create_index("ix_model_version_status", "model_version", ["status"])
        op.create_index("ix_model_version_trained_at", "model_version", ["trained_at"])

    # model_metric
    if not insp.has_table("model_metric"):
        op.create_table(
            "model_metric",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column(
                "model_version_id", sa.Integer, sa.ForeignKey("model_version.id"), nullable=False
            ),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("value", sa.Float, nullable=False, server_default="0"),
            sa.Column("observed_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_model_metric_model_version_id", "model_metric", ["model_version_id"])
        op.create_index("ix_model_metric_name", "model_metric", ["name"])
        op.create_index("ix_model_metric_observed_at", "model_metric", ["observed_at"])

    # drift_report
    if not insp.has_table("drift_report"):
        op.create_table(
            "drift_report",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column(
                "model_version_id", sa.Integer, sa.ForeignKey("model_version.id"), nullable=False
            ),
            sa.Column("brain_id", sa.String(64), nullable=False),
            sa.Column("summary", sa.Text, nullable=True),
            sa.Column("severity", sa.String(32), nullable=False, server_default="low"),
            sa.Column("detected_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_drift_report_model_version_id", "drift_report", ["model_version_id"])
        op.create_index("ix_drift_report_brain_id", "drift_report", ["brain_id"])
        op.create_index("ix_drift_report_severity", "drift_report", ["severity"])
        op.create_index("ix_drift_report_detected_at", "drift_report", ["detected_at"])

    # benchmark_run
    if not insp.has_table("benchmark_run"):
        op.create_table(
            "benchmark_run",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column(
                "model_version_id", sa.Integer, sa.ForeignKey("model_version.id"), nullable=False
            ),
            sa.Column("name", sa.String(64), nullable=False),
            sa.Column("dataset_ref", sa.String(128), nullable=True),
            sa.Column("score", sa.Float, nullable=True),
            sa.Column("report", sa.Text, nullable=True),
            sa.Column("ran_at", sa.DateTime, nullable=True),
        )
        op.create_index("ix_benchmark_run_model_version_id", "benchmark_run", ["model_version_id"])
        op.create_index("ix_benchmark_run_name", "benchmark_run", ["name"])
        op.create_index("ix_benchmark_run_ran_at", "benchmark_run", ["ran_at"])

    # rollout_state
    if not insp.has_table("rollout_state"):
        op.create_table(
            "rollout_state",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
            sa.Column(
                "model_version_id", sa.Integer, sa.ForeignKey("model_version.id"), nullable=False
            ),
            sa.Column("brain_id", sa.String(64), nullable=False),
            sa.Column("phase", sa.String(32), nullable=False, server_default="shadow"),
            sa.Column("percent", sa.Integer, nullable=False, server_default="0"),
            sa.Column("updated_at_ts", sa.DateTime, nullable=True),
        )
        op.create_index("ix_rollout_state_model_version_id", "rollout_state", ["model_version_id"])
        op.create_index("ix_rollout_state_brain_id", "rollout_state", ["brain_id"])
        op.create_index("ix_rollout_state_phase", "rollout_state", ["phase"])


def downgrade() -> None:
    # Drop in reverse order of dependencies
    op.drop_index("ix_rollout_state_phase", table_name="rollout_state")
    op.drop_index("ix_rollout_state_brain_id", table_name="rollout_state")
    op.drop_index("ix_rollout_state_model_version_id", table_name="rollout_state")
    op.drop_table("rollout_state")

    op.drop_index("ix_benchmark_run_ran_at", table_name="benchmark_run")
    op.drop_index("ix_benchmark_run_name", table_name="benchmark_run")
    op.drop_index("ix_benchmark_run_model_version_id", table_name="benchmark_run")
    op.drop_table("benchmark_run")

    op.drop_index("ix_drift_report_detected_at", table_name="drift_report")
    op.drop_index("ix_drift_report_severity", table_name="drift_report")
    op.drop_index("ix_drift_report_brain_id", table_name="drift_report")
    op.drop_index("ix_drift_report_model_version_id", table_name="drift_report")
    op.drop_table("drift_report")

    op.drop_index("ix_model_metric_observed_at", table_name="model_metric")
    op.drop_index("ix_model_metric_name", table_name="model_metric")
    op.drop_index("ix_model_metric_model_version_id", table_name="model_metric")
    op.drop_table("model_metric")

    op.drop_index("ix_model_version_trained_at", table_name="model_version")
    op.drop_index("ix_model_version_status", table_name="model_version")
    op.drop_index("ix_model_version_version", table_name="model_version")
    op.drop_index("ix_model_version_brain_id", table_name="model_version")
    op.drop_index("ix_model_version_org_id", table_name="model_version")
    op.drop_table("model_version")

    op.drop_index("ix_feature_snapshot_observed_at", table_name="feature_snapshot")
    op.drop_index("ix_feature_snapshot_feature_key", table_name="feature_snapshot")
    op.drop_index("ix_feature_snapshot_brain_id", table_name="feature_snapshot")
    op.drop_index("ix_feature_snapshot_org_id", table_name="feature_snapshot")
    op.drop_table("feature_snapshot")
