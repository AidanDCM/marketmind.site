"""Database setup and migration utility."""

import os
import site
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
sys.path.insert(0, project_root)

# Add the virtual environment's site-packages to the Python path
venv_path = os.path.join(project_root, ".venv")
site_packages = os.path.join(
    venv_path, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"
)
if os.path.exists(site_packages):
    site.addsitedir(site_packages)
    sys.path.append(site_packages)

# Now import the required modules
try:
    from dotenv import load_dotenv

    from alembic import command
    from alembic.config import Config
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print(f"Python path: {sys.path}")
    raise

# Load environment variables from .env file if it exists
load_dotenv()


def get_database_url() -> str:
    """Get the database URL from environment variables."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Default to SQLite if no URL is provided
        db_path = os.path.join(project_root, "marketmind.db")
        db_url = f"sqlite:///{db_path}"
    return db_url


def init_database():
    """Initialize the database and create all tables."""
    from packages.database.base import init_db

    db_url = get_database_url()
    print(f"Initializing database at: {db_url}")

    # Create all tables
    init_db(db_url)

    # Set up Alembic
    alembic_cfg = Config(os.path.join(project_root, "alembic.ini"))

    # Set the database URL in the Alembic config
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Generate the initial migration
    print("Generating initial migration...")
    command.revision(
        alembic_cfg,
        autogenerate=True,
        message="Initial migration",
    )

    # Run the migration
    print("Running migrations...")
    command.upgrade(alembic_cfg, "head")

    print("Database setup complete!")


if __name__ == "__main__":
    init_database()
