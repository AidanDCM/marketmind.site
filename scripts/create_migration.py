#!/usr/bin/env python3
"""
Script to create database migrations.

This script sets up the Alembic environment and generates a new migration.
"""

import os
import sys

from alembic import command
from alembic.config import Config


def create_migration(message: str = "auto"):
    """Create a new database migration.

    Args:
        message: Description of the migration
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # Generate the migration
    command.revision(config, autogenerate=True, message=message)


if __name__ == "__main__":
    # Default migration message
    message = "auto"

    # Use the first command-line argument as the migration message if provided
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])

    # Create the migration
    create_migration(message)
