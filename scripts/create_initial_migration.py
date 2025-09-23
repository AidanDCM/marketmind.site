#!/usr/bin/env python3
"""
Script to create and apply the initial database migration.
"""

import os
import sys

from sqlalchemy import create_engine, text

from alembic import command
from alembic.config import Config


def create_initial_migration():
    """Create and apply the initial database migration."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Add the project root to the Python path
    sys.path.insert(0, project_root)

    # Import models to ensure they are registered with SQLAlchemy
    from packages.shared.models import Base

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

    # Set the target metadata
    target_metadata = Base.metadata
    config.attributes["target_metadata"] = target_metadata

    # Create the migrations directory if it doesn't exist
    versions_dir = os.path.join(project_root, "alembic", "versions")
    os.makedirs(versions_dir, exist_ok=True)

    # Create an initial migration
    print("Creating initial migration...")
    command.revision(config, autogenerate=True, message="Initial schema with core models")

    # Apply the migration
    print("Applying migration...")
    command.upgrade(config, "head")

    print("Migration created and applied successfully!")


if __name__ == "__main__":
    create_initial_migration()
