#!/usr/bin/env python3
"""
Script to completely reset the database and create a fresh migration.
"""

import os

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config


def reset_everything():
    """Completely reset the database and create a fresh migration."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database URL
    db_url = "sqlite:///./marketmind.db"
    db_path = os.path.join(project_root, "marketmind.db")

    # Remove the database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed database file: {db_path}")

    # Remove the migrations directory if it exists
    versions_dir = os.path.join(project_root, "alembic", "versions")
    if os.path.exists(versions_dir):
        for f in os.listdir(versions_dir):
            if f.endswith(".py") and f != "__pycache__":
                os.remove(os.path.join(versions_dir, f))
        print(f"Cleared migrations directory: {versions_dir}")

    # Create a new database
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # Create an initial migration
    print("Creating initial migration...")
    command.revision(config, autogenerate=True, message="Initial schema with core models")

    # Apply the migration
    print("Applying migration...")
    command.upgrade(config, "head")

    print("Database reset and migration applied successfully!")


if __name__ == "__main__":
    reset_everything()
