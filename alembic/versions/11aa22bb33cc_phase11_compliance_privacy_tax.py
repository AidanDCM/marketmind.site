"""phase11 compliance/privacy/tax schema

Revision ID: 11aa22bb33cc
Revises: 5133ca011da5
Create Date: 2025-08-22

Creates Phase 11 tables:
- compliance_pack
- restricted_term
- restricted_category
- map_catalog
- listing_compliance_state
- compliance_violation
- privacy_request
- erasure_job
- tax_attestation
- listing_snapshot
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "11aa22bb33cc"
down_revision: Union[str, Sequence[str], None] = "5133ca011da5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_pack",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("scope", sa.String(50), nullable=False, server_default="global"),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("source_uri", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "restricted_term",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pack_id", sa.Integer, nullable=False),
        sa.Column("term", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False, server_default="term"),
        sa.Column("locale", sa.String(10), nullable=False, server_default="en_US"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warn"),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("ix_restricted_term_pack", "restricted_term", ["pack_id"])
    op.create_index("ix_restricted_term_term", "restricted_term", ["term"])
    op.create_index("ix_restricted_term_locale", "restricted_term", ["locale"])

    op.create_table(
        "restricted_category",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("pack_id", sa.Integer, nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(200), nullable=False),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("ix_restricted_category_pack", "restricted_category", ["pack_id"])
    op.create_index("ix_restricted_category_channel", "restricted_category", ["channel"])
    op.create_index("ix_restricted_category_code", "restricted_category", ["code"])

    op.create_table(
        "map_catalog",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("supplier_id", sa.Integer, nullable=True),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("map_cents", sa.Integer, nullable=False),
        sa.Column("effective_from", sa.DateTime, nullable=True),
        sa.Column("effective_to", sa.DateTime, nullable=True),
    )
    op.create_index("ix_map_catalog_supplier", "map_catalog", ["supplier_id"])
    op.create_index("ix_map_catalog_brand", "map_catalog", ["brand"])
    op.create_index("ix_map_catalog_sku", "map_catalog", ["sku"], unique=False)

    op.create_table(
        "listing_compliance_state",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("org_id", sa.String(32), nullable=False),
        sa.Column("brain_id", sa.String(32), nullable=False),
        sa.Column("product_id", sa.Integer, nullable=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("listing_ref", sa.String(100), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="ok"),
        sa.Column("reasons", sa.Text, nullable=False, server_default="[]"),
        sa.Column("last_reviewed_at", sa.DateTime, nullable=True),
    )
    op.create_index(
        "ix_listing_compliance_org",
        "listing_compliance_state",
        ["org_id", "brain_id"],
    )
    op.create_index(
        "ix_listing_compliance_ref",
        "listing_compliance_state",
        ["channel", "listing_ref"],
    )
    op.create_index(
        "ix_listing_compliance_product",
        "listing_compliance_state",
        ["product_id"],
    )

    op.create_table(
        "compliance_violation",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("listing_ref", sa.String(100), nullable=False),
        sa.Column("vtype", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warn"),
        sa.Column("details", sa.Text, nullable=False, server_default="{}"),
        sa.Column("action", sa.String(50), nullable=False, server_default="observe"),
        sa.Column("incident_id", sa.Integer, nullable=True),
    )
    op.create_index("ix_compliance_violation_ts", "compliance_violation", ["ts"])
    op.create_index("ix_compliance_violation_channel", "compliance_violation", ["channel"])
    op.create_index("ix_compliance_violation_ref", "compliance_violation", ["listing_ref"])
    op.create_index("ix_compliance_violation_type", "compliance_violation", ["vtype"])
    op.create_index("ix_compliance_violation_incident", "compliance_violation", ["incident_id"])

    op.create_table(
        "privacy_request",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ts", sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column("rtype", sa.String(50), nullable=False),
        sa.Column("subject_ref", sa.String(200), nullable=False),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("result_uri", sa.String(500), nullable=False, server_default=""),
        sa.Column("notes", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("ix_privacy_request_ts", "privacy_request", ["ts"])
    op.create_index("ix_privacy_request_subject", "privacy_request", ["subject_ref"])

    op.create_table(
        "erasure_job",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("request_id", sa.Integer, nullable=False),
        sa.Column("target", sa.String(100), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("counts", sa.Text, nullable=False, server_default="{}"),
        sa.Column("finished_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_erasure_job_request", "erasure_job", ["request_id"])

    op.create_table(
        "tax_attestation",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("jurisdiction", sa.String(50), nullable=False),
        sa.Column("model", sa.String(50), nullable=False),
        sa.Column("total_tax_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("attester", sa.String(100), nullable=False),
        sa.Column("attested_at", sa.DateTime, nullable=True),
        sa.Column("evidence_uri", sa.String(500), nullable=False, server_default=""),
    )
    op.create_index("ix_tax_attestation_period", "tax_attestation", ["period"])
    op.create_index("ix_tax_attestation_juris", "tax_attestation", ["jurisdiction"])

    op.create_table(
        "listing_snapshot",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("listing_ref", sa.String(100), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("captured_at", sa.DateTime, nullable=True, server_default=sa.func.now()),
        sa.Column("content", sa.Text, nullable=False, server_default="{}"),
        sa.Column("images", sa.Text, nullable=False, server_default="[]"),
        sa.Column("price_cents", sa.Integer, nullable=True),
        sa.Column("meta", sa.Text, nullable=False, server_default="{}"),
    )
    op.create_index("ix_listing_snapshot_ref", "listing_snapshot", ["listing_ref"])
    op.create_index("ix_listing_snapshot_channel", "listing_snapshot", ["channel"])
    op.create_index("ix_listing_snapshot_captured", "listing_snapshot", ["captured_at"])


def downgrade() -> None:
    op.drop_index("ix_listing_snapshot_captured", table_name="listing_snapshot")
    op.drop_index("ix_listing_snapshot_channel", table_name="listing_snapshot")
    op.drop_index("ix_listing_snapshot_ref", table_name="listing_snapshot")
    op.drop_table("listing_snapshot")

    op.drop_index("ix_tax_attestation_juris", table_name="tax_attestation")
    op.drop_index("ix_tax_attestation_period", table_name="tax_attestation")
    op.drop_table("tax_attestation")

    op.drop_index("ix_erasure_job_request", table_name="erasure_job")
    op.drop_table("erasure_job")

    op.drop_index("ix_privacy_request_subject", table_name="privacy_request")
    op.drop_index("ix_privacy_request_ts", table_name="privacy_request")
    op.drop_table("privacy_request")

    op.drop_index("ix_compliance_violation_incident", table_name="compliance_violation")
    op.drop_index("ix_compliance_violation_type", table_name="compliance_violation")
    op.drop_index("ix_compliance_violation_ref", table_name="compliance_violation")
    op.drop_index("ix_compliance_violation_channel", table_name="compliance_violation")
    op.drop_index("ix_compliance_violation_ts", table_name="compliance_violation")
    op.drop_table("compliance_violation")

    op.drop_index("ix_listing_compliance_product", table_name="listing_compliance_state")
    op.drop_index("ix_listing_compliance_ref", table_name="listing_compliance_state")
    op.drop_index("ix_listing_compliance_org", table_name="listing_compliance_state")
    op.drop_table("listing_compliance_state")

    op.drop_index("ix_map_catalog_sku", table_name="map_catalog")
    op.drop_index("ix_map_catalog_brand", table_name="map_catalog")
    op.drop_index("ix_map_catalog_supplier", table_name="map_catalog")
    op.drop_table("map_catalog")

    op.drop_index("ix_restricted_category_code", table_name="restricted_category")
    op.drop_index("ix_restricted_category_channel", table_name="restricted_category")
    op.drop_index("ix_restricted_category_pack", table_name="restricted_category")
    op.drop_table("restricted_category")

    op.drop_index("ix_restricted_term_locale", table_name="restricted_term")
    op.drop_index("ix_restricted_term_term", table_name="restricted_term")
    op.drop_index("ix_restricted_term_pack", table_name="restricted_term")
    op.drop_table("restricted_term")

    op.drop_table("compliance_pack")
