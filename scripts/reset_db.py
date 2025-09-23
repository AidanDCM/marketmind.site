#!/usr/bin/env python3
"""
Script to reset the database to a clean state.
"""

import os

from sqlalchemy import create_engine, text


def reset_database():
    """Reset the database to a clean state."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Database URL
    db_url = "sqlite:///./marketmind.db"

    # Remove the database file if it exists
    db_path = os.path.join(project_root, "marketmind.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed database file: {db_path}")

    # Create a new database
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()

    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()
