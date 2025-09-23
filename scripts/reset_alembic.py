#!/usr/bin/env python3
"""
Script to reset Alembic version tracking.
"""

import os

from sqlalchemy import create_engine, text


def reset_alembic():
    """Reset Alembic version tracking."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database URL
    db_url = "sqlite:///./marketmind.db"

    # Create the database engine
    engine = create_engine(db_url)

    # Drop the alembic_version table if it exists
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()

    print("Alembic version tracking has been reset.")


if __name__ == "__main__":
    reset_alembic()
