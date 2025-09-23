#!/usr/bin/env python3
"""
Script to check database state and apply migrations.
"""

import os

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config


def check_database():
    """Check database state and apply migrations if needed."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # Check if the database exists and has tables
    db_url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"Database URL: {db_url}")
    print(f"Existing tables: {tables}")

    if "alembic_version" not in tables:
        print("Alembic version table not found. Initializing database...")
        command.stamp(config, "head")

    # Show current migration state
    print("\nCurrent migration state:")
    command.current(config)

    # Show available migrations
    print("\nAvailable migrations:")
    command.history(config)

    # Check for pending migrations
    print("\nPending migrations:")
    command.heads(config)

    # Apply any pending migrations
    print("\nApplying pending migrations...")
    command.upgrade(config, "head")

    print("\nMigration complete.")


if __name__ == "__main__":
    check_database()
