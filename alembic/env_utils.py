"""Alembic environment utilities for MarketMind.

This module provides helper functions for the Alembic migration environment.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def get_metadata():
    """Get SQLAlchemy metadata with all models imported.

    This function imports all models to ensure they are registered with SQLAlchemy's
    metadata before Alembic generates migrations.
    """
    # Import Base from the active models package to ensure they are registered
    # with SQLAlchemy before Alembic autogenerates migrations.
    from packages.database.models import Base

    return Base.metadata
