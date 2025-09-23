#!/usr/bin/env python3
"""
Run a one-off ingestion locally without Celery/Worker.
Writes sample product/supplier/price_history rows.
"""

from apps.hive_worker.tasks.ingest import run_ingest
from packages.shared.db import Base, get_engine


def main():
    # Ensure tables exist (local dev convenience)
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    # Call the task function directly to exercise adapter path
    run_ingest()
    print("[local] Ingest completed")


if __name__ == "__main__":
    main()
