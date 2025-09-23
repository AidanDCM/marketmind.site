"""Database configuration and utilities.

This module provides database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .models.base import Base

# Database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
ScopedSession = scoped_session(SessionLocal)


def init_db(database_url: str) -> None:
    """Initialize the database connection and create tables.

    Args:
        database_url: The database connection URL
    """
    # Create the database engine
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Configure the session factory to use this engine
    SessionLocal.configure(bind=engine)


def get_db():
    """Dependency for getting a database session.

    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
