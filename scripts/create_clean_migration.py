#!/usr/bin/env python3
"""
Script to create a clean migration for the current schema.
"""

import os
import sys

from alembic import command
from alembic.config import Config


def create_clean_migration(message: str = "Initial schema"):
    """Create a clean migration for the current schema.

    Args:
        message: Description of the migration
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # First, create a revision with the current models
    command.revision(config, autogenerate=True, message=message)

    # Get the revision ID from the newly created migration
    # (this is a bit of a hack, but it works for our purposes)
    versions_dir = os.path.join(project_root, "alembic", "versions")
    migrations = sorted([f for f in os.listdir(versions_dir) if f.endswith(".py")])
    if not migrations:
        print("No migration files found!")
        return

    latest_migration = os.path.join(versions_dir, migrations[-1])
    print(f"Created migration: {latest_migration}")


if __name__ == "__main__":
    # Default migration message
    message = "Initial schema with core models"

    # Use the first command-line argument as the migration message if provided
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])

    # Create the migration
    create_clean_migration(message)
