#!/usr/bin/env python3
"""
Script to initialize the database and apply migrations.
"""

import os

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config


def init_database():
    """Initialize the database and apply migrations."""
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
    command.stamp(config, "base")

    # Generate an initial migration
    migration_message = "Initial database schema with core models"
    command.revision(config, autogenerate=True, message=migration_message)

    # Apply the migration
    command.upgrade(config, "head")

    print("Database initialization complete.")


if __name__ == "__main__":
    init_database()
