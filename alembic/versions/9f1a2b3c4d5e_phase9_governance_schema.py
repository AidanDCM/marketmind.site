"""phase9_governance_schema

Revision ID: 9f1a2b3c4d5e
Revises: 061edfd5cfd8
Create Date: 2025-08-22 17:35:00.000000+00:00

Create core governance tables:
- policy_rule
- governance_decision
- risk_event (partition-ready fields)
- incident
- api_contract
- release_rollout
- chaos_experiment
- kpi_threshold
- slo_budget
- security_finding
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9f1a2b3c4d5e"
down_revision = "061edfd5cfd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_rule",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="100"),
        sa.Column("scope", sa.String(50), nullable=False, server_default="global"),
        sa.Column("match_expr", sa.Text, nullable=False),  # DSL / JSONLogic / CEL
        sa.Column("action", sa.String(20), nullable=False),  # allow|deny|warn
        sa.Column("metadata", sa.Text, nullable=False, server_default="{}"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_policy_rule_org_priority", "policy_rule", ["org_id", "priority"])

    op.create_table(
        "governance_decision",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(64), nullable=False),
        sa.Column("policy_hits", sa.Text, nullable=False, server_default="[]"),  # JSON list
        sa.Column("risk_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("decision", sa.String(20), nullable=False),  # proceed|block|simulate
        sa.Column("confidence", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("context", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index(
        "ix_governance_decision_entity",
        "governance_decision",
        ["org_id", "entity_type", "entity_id", "created_at"],
    )

    op.create_table(
        "risk_event",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),  # system, adapter, rule
        sa.Column("signal", sa.String(100), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),  # info|low|med|high|critical
        sa.Column("value", sa.Float),
        sa.Column("metadata", sa.Text, nullable=False, server_default="{}"),
        sa.Column(
            "timestamp", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_risk_event_org_time", "risk_event", ["org_id", "timestamp"])

    op.create_table(
        "incident",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("labels", sa.Text, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("resolved_at", sa.DateTime),
    )
    op.create_index("ix_incident_org_status", "incident", ["org_id", "status", "created_at"])

    op.create_table(
        "api_contract",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),  # cj|amazon|sheets|internal
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("schema_hash", sa.String(64), nullable=False),
        sa.Column("schema", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_api_contract_provider", "api_contract", ["org_id", "provider", "version"])

    op.create_table(
        "release_rollout",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("component", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("cohort", sa.Float, nullable=False),  # 0.01 for 1%
        sa.Column("metrics", sa.Text, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="started"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("finished_at", sa.DateTime),
    )
    op.create_index(
        "ix_release_rollout_component", "release_rollout", ["org_id", "component", "created_at"]
    )

    op.create_table(
        "chaos_experiment",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("scenario", sa.String(100), nullable=False),
        sa.Column("params", sa.Text, nullable=False, server_default="{}"),
        sa.Column("result", sa.Text, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )

    op.create_table(
        "kpi_threshold",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("kpi", sa.String(100), nullable=False),
        sa.Column("threshold", sa.Float, nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),  # above|below
        sa.Column("window", sa.String(20), nullable=False),  # e.g., 5m, 1h
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_kpi_threshold_kpi", "kpi_threshold", ["org_id", "kpi"])

    op.create_table(
        "slo_budget",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("slo", sa.String(100), nullable=False),
        sa.Column("error_budget", sa.Float, nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )
    op.create_index("ix_slo_budget_slo", "slo_budget", ["org_id", "slo"])

    op.create_table(
        "security_finding",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),  # secrets|deps|access|policy
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("details", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("resolved_at", sa.DateTime),
    )
    op.create_index(
        "ix_security_finding_cat",
        "security_finding",
        ["org_id", "category", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_security_finding_cat", table_name="security_finding")
    op.drop_table("security_finding")

    op.drop_index("ix_slo_budget_slo", table_name="slo_budget")
    op.drop_table("slo_budget")

    op.drop_index("ix_kpi_threshold_kpi", table_name="kpi_threshold")
    op.drop_table("kpi_threshold")

    op.drop_table("chaos_experiment")

    op.drop_index("ix_release_rollout_component", table_name="release_rollout")
    op.drop_table("release_rollout")

    op.drop_index("ix_api_contract_provider", table_name="api_contract")
    op.drop_table("api_contract")

    op.drop_index("ix_incident_org_status", table_name="incident")
    op.drop_table("incident")

    op.drop_index("ix_risk_event_org_time", table_name="risk_event")
    op.drop_table("risk_event")

    op.drop_index("ix_governance_decision_entity", table_name="governance_decision")
    op.drop_table("governance_decision")

    op.drop_index("ix_policy_rule_org_priority", table_name="policy_rule")
    op.drop_table("policy_rule")
