#!/usr/bin/env python3
"""
Script to apply database migrations.
"""

import os

from alembic import command
from alembic.config import Config


def apply_migrations():
    """Apply all pending migrations."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Set up the Alembic configuration
    config = Config(os.path.join(project_root, "alembic.ini"))
    config.set_main_option("script_location", os.path.join(project_root, "alembic"))

    # Apply all pending migrations
    command.upgrade(config, "head")
    print("Migrations applied successfully.")


if __name__ == "__main__":
    apply_migrations()
