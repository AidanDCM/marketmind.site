#!/usr/bin/env python3
"""
Script to create a fresh migration for the current schema.
"""

import os

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config


def create_fresh_migration():
    """Create a fresh migration for the current schema."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database URL
    db_url = "sqlite:///./marketmind.db"

    # Create the database engine
    engine = create_engine(db_url)

    # Initialize the database with PRAGMA settings
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # Stamp the database with the base revision
    print("Stamping database with base revision...")
    command.stamp(config, "base")

    # Create a new migration
    print("Generating migration...")
    migration_message = "Initial database schema with core models"
    command.revision(config, autogenerate=True, message=migration_message)

    # Apply the migration
    print("Applying migration...")
    command.upgrade(config, "head")

    print("Migration created and applied successfully.")


if __name__ == "__main__":
    create_fresh_migration()
