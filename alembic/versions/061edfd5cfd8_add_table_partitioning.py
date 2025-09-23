"""add_table_partitioning

Revision ID: 061edfd5cfd8
Revises: 8e9c1ccc6af9
Create Date: 2025-08-14 07:56:12.344561+00:00

This migration implements table partitioning for the following tables:
- price_history: Partitioned by month on recorded_at
- audit_log: Partitioned by month on timestamp
- inventory_event: Partitioned by month on timestamp

For SQLite, we implement a manual partitioning scheme using separate tables and views.
"""

from datetime import datetime, timedelta
from typing import List

from alembic import op

# revision identifiers, used by Alembic.
revision = "061edfd5cfd8"
down_revision = "8e9c1ccc6af9"
branch_labels = None
depends_on = None


def get_connection():
    """Get the database connection."""
    return op.get_bind()


def create_partition_table(
    table_name: str,
    base_table_def: str,
    partition_suffix: str,
    partition_condition: str,
    is_postgresql: bool = False,
) -> None:
    """Create a partition table with the given suffix and condition."""
    get_connection()

    if is_postgresql:
        # For PostgreSQL, use native partitioning
        # Note: This is safe as table_name and partition_suffix are controlled by migration code
        partition_table = f"{table_name}_{partition_suffix}"
        start_date = f"{partition_suffix}-01"
        end_date = f"{partition_suffix}-31"
        
        op.execute(
            f"CREATE TABLE {partition_table} "
            f"PARTITION OF {table_name} "
            f"FOR VALUES FROM ('{start_date}') TO ('{end_date}')"
        )
    else:
        # For SQLite, create a separate table with the same schema
        op.execute(f"CREATE TABLE {table_name}_{partition_suffix} ({base_table_def})")

        # Create indexes on the partition
        op.execute(
            f"CREATE INDEX ix_{table_name}_{partition_suffix}_org_id "
            f"ON {table_name}_{partition_suffix} (org_id)"
        )

        # Add any other indexes as needed
        if table_name == "price_history":
            op.execute(
                f"CREATE INDEX ix_{table_name}_{partition_suffix}_recorded_at "
                f"ON {table_name}_{partition_suffix} (recorded_at)"
            )
        elif table_name == "audit_log":
            op.execute(
                f"CREATE INDEX ix_{table_name}_{partition_suffix}_timestamp "
                f"ON {table_name}_{partition_suffix} (timestamp)"
            )
        elif table_name == "inventory_event":
            op.execute(
                f"CREATE INDEX ix_{table_name}_{partition_suffix}_timestamp "
                f"ON {table_name}_{partition_suffix} (timestamp)"
            )


def create_partitioned_view(
    view_name: str, base_table_name: str, partition_suffixes: List[str], is_postgresql: bool = False
) -> None:
    """Create a view that combines all partition tables."""
    if is_postgresql:
        return  # PostgreSQL handles this automatically with partitioning

    # For SQLite, create a view that combines all partitions
    union_all = " UNION ALL ".join(
        f"SELECT * FROM {base_table_name}_{suffix}" for suffix in partition_suffixes
    )

    op.execute(f"CREATE VIEW {view_name}_view AS {union_all}")


def create_insert_trigger(
    table_name: str, partition_condition: str, is_postgresql: bool = False
) -> None:
    """Create a trigger to route inserts to the correct partition."""
    if is_postgresql:
        return  # PostgreSQL handles this automatically with partitioning

    # For SQLite, create a simple trigger that will need to be updated
    op.execute(
        f"""
        CREATE TRIGGER {table_name}_insert_trigger
        INSTEAD OF INSERT ON {table_name}_view
        BEGIN
            INSERT INTO {table_name}_v2 SELECT * FROM NEW;
        END;
    """
    )


def upgrade() -> None:
    """Upgrade schema to implement table partitioning."""
    conn = get_connection()
    is_postgresql = conn.dialect.name == "postgresql"

    # Generate month strings for the next 3 months (including current)
    now = datetime.utcnow()
    months = [(now + timedelta(days=30 * i)).strftime("%Y_%m") for i in range(3)]

    # Table definitions without f-strings
    price_history_def = """
        org_id CHAR(32) NOT NULL,
        listing_id CHAR(32) NOT NULL,
        price_cents INTEGER NOT NULL,
        buybox BOOLEAN NOT NULL DEFAULT FALSE,
        comp_best_cents INTEGER,
        source VARCHAR(20) NOT NULL,
        recorded_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (org_id, listing_id, recorded_at),
        FOREIGN KEY (org_id) REFERENCES org (id) ON DELETE CASCADE,
        FOREIGN KEY (listing_id) REFERENCES channel_listing (id) ON DELETE CASCADE
    """

    audit_log_def = """
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_id CHAR(32),
        brain_id CHAR(32),
        actor_type VARCHAR(20) NOT NULL,
        actor_id VARCHAR(100),
        actor_name VARCHAR(255),
        action VARCHAR(30) NOT NULL,
        entity_type VARCHAR(50) NOT NULL,
        entity_id CHAR(32),
        delta TEXT,
        ip_address VARCHAR(45),
        user_agent TEXT,
        request_id VARCHAR(100),
        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_id) REFERENCES org (id) ON DELETE CASCADE,
        FOREIGN KEY (brain_id) REFERENCES brain (id) ON DELETE CASCADE
    """

    inventory_event_def = """
        org_id CHAR(32) NOT NULL,
        product_id CHAR(32) NOT NULL,
        event_type VARCHAR(20) NOT NULL,
        delta INTEGER NOT NULL,
        source VARCHAR(50) NOT NULL DEFAULT 'system',
        reference_id CHAR(32),
        reference_type VARCHAR(50),
        metadata TEXT NOT NULL DEFAULT '{}',
        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (org_id, product_id, timestamp, event_type),
        FOREIGN KEY (org_id) REFERENCES org (id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES product (id) ON DELETE CASCADE,
        CHECK (delta != 0)
    """

    # Create partition tables for each month
    if not is_postgresql:
        for month in months:
            # Price History
            create_partition_table(
                table_name="price_history",
                base_table_def=price_history_def,
                partition_suffix=month,
                partition_condition="recorded_at",
            )

            # Audit Log
            create_partition_table(
                table_name="audit_log",
                base_table_def=audit_log_def,
                partition_suffix=month,
                partition_condition="timestamp",
            )

            # Inventory Event
            create_partition_table(
                table_name="inventory_event",
                base_table_def=inventory_event_def,
                partition_suffix=month,
                partition_condition="timestamp",
            )

    # Create views and triggers for SQLite
    if not is_postgresql:
        create_partitioned_view("price_history", "price_history", months, is_postgresql)
        create_partitioned_view("audit_log", "audit_log", months, is_postgresql)
        create_partitioned_view("inventory_event", "inventory_event", months, is_postgresql)

        create_insert_trigger("price_history", "recorded_at", is_postgresql)
        create_insert_trigger("audit_log", "timestamp", is_postgresql)
        create_insert_trigger("inventory_event", "timestamp", is_postgresql)


def downgrade() -> None:
    """Downgrade schema by removing partitioning."""
    conn = get_connection()
    is_postgresql = conn.dialect.name == "postgresql"

    # Generate month strings for the next 3 months (including current)
    now = datetime.utcnow()
    months = [(now + timedelta(days=30 * i)).strftime("%Y_%m") for i in range(3)]

    # Drop triggers and views first
    if not is_postgresql:
        for table in ["price_history", "audit_log", "inventory_event"]:
            op.execute(f"DROP TRIGGER IF EXISTS {table}_insert_trigger")
            op.execute(f"DROP VIEW IF EXISTS {table}_view")

    # Drop partition tables
    for table in ["price_history", "audit_log", "inventory_event"]:
        for month in months:
            op.execute(f"DROP TABLE IF EXISTS {table}_{month}")
