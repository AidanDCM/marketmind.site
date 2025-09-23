"""phase12 marketing campaign table

Revision ID: 12ab34cd56ef
Revises: 11aa22bb33cc
Create Date: 2025-08-22

Creates Phase 12 table:
- campaign
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "12ab34cd56ef"
down_revision: Union[str, Sequence[str], None] = "11aa22bb33cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaign",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("org_id", sa.String(64), nullable=True),
        sa.Column("brain_id", sa.String(64), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("start_at", sa.DateTime, nullable=True),
        sa.Column("end_at", sa.DateTime, nullable=True),
        sa.Column("meta", sa.Text, nullable=True),
    )
    op.create_index("ix_campaign_org_id", "campaign", ["org_id"])
    op.create_index("ix_campaign_brain_id", "campaign", ["brain_id"])
    op.create_index("ix_campaign_status", "campaign", ["status"])


def downgrade() -> None:
    op.drop_index("ix_campaign_status", table_name="campaign")
    op.drop_index("ix_campaign_brain_id", table_name="campaign")
    op.drop_index("ix_campaign_org_id", table_name="campaign")
    op.drop_table("campaign")
