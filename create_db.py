"""Utility script to create the database if it doesn't exist."""

import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_database():
    """Create the database if it doesn't exist."""
    # Get database connection parameters
    db_url = os.getenv("DB_URL")
    if not db_url:
        logger.error("DB_URL not found in environment variables")
        return False

    # Parse the database URL
    from urllib.parse import urlparse

    result = urlparse(db_url)
    db_name = result.path[1:]  # Remove the leading '/'

    # Connect to the default 'postgres' database to create our database
    conn = psycopg2.connect(
        dbname="postgres",
        user=result.username or "postgres",
        password=result.password or "postgres",
        host=result.hostname or "localhost",
        port=result.port or "5432",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        # Check if database exists
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            exists = cursor.fetchone()

            if not exists:
                logger.info(f"Creating database: {db_name}")
                # Use identifier quoting for database name to prevent SQL injection
                from psycopg2 import sql
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                logger.info("Database created successfully")
            else:
                logger.info(f"Database {db_name} already exists")

        return True
    except Exception as e:
        logger.error(f"Error creating database: {e}", exc_info=True)
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    create_database()
