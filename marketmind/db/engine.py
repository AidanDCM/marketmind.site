"""Slice 11: SQLAlchemy engine and session factory.

DATABASE_URL defaults to SQLite at data/marketmind.db (relative to cwd).
Override with the DATABASE_URL environment variable.

Tests should pass an in-memory URL:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
"""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", "sqlite:///data/marketmind.db")


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    # StaticPool is required for in-memory SQLite: ensures all sessions share
    # the same connection so schema created by create_all() is visible everywhere.
    if url == "sqlite:///:memory:":
        return create_engine(url, connect_args=connect_args, poolclass=StaticPool)
    return create_engine(url, connect_args=connect_args, echo=False)


@contextmanager
def session_scope(engine: Engine) -> Generator[Session, None, None]:
    """Yield a transactional Session; commit on success, rollback on error."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
