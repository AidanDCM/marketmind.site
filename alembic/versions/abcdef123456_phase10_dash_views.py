"""phase10 dash views

Revision ID: abcdef123456
Revises: 9f1a2b3c4d5e
Create Date: 2025-08-22
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection

from alembic import op

# revision identifiers, used by Alembic.
revision = "abcdef123456"
down_revision = "9f1a2b3c4d5e"
branch_labels = None
depends_on = None


VIEW_SQL = """
    CREATE OR REPLACE VIEW v_dash_sales_kpis AS
    SELECT
      o.org_id,
      o.brain_id,
      COUNT(*) AS orders,
      COALESCE(SUM(o.net_revenue_cents), 0) AS net_revenue_cents,
      CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(o.net_revenue_cents),0) / COUNT(*) ELSE 0 END AS aov_cents
    FROM "order" o
    GROUP BY o.org_id, o.brain_id
    """

DROP_SQL = "DROP VIEW IF EXISTS v_dash_sales_kpis"


def _is_postgres(conn: Connection) -> bool:
    try:
        return conn.dialect.name == "postgresql"
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        # SQLite and others: skip view creation to remain portable
        return
    conn.execute(text(VIEW_SQL))


def downgrade() -> None:
    conn = op.get_bind()
    if not _is_postgres(conn):
        return
    conn.execute(text(DROP_SQL))
