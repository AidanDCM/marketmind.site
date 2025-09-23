#!/usr/bin/env python3
"""
Script to set up the configuration audit database table.

This script creates the necessary database tables for the config audit trail.
It should be run during application setup or after database migrations.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_audit_db():
    """Create the config audit database tables."""
    try:
        from packages.shared.config.audit import AuditTrail
        from packages.shared.config.loader import get_settings

        # Get database URL from settings
        settings = get_settings()
        db_url = settings.db.url

        logger.info(f"Setting up config audit database at: {db_url}")

        # Initialize audit trail to create tables
        audit_trail = AuditTrail(db_url=db_url)

        logger.info("Successfully created config audit database tables")
        return True

    except Exception as e:
        logger.error(f"Failed to set up config audit database: {e}")
        return False


if __name__ == "__main__":
    success = setup_audit_db()
    sys.exit(0 if success else 1)
