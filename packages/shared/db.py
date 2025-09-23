from __future__ import annotations

import warnings
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

from packages.shared.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    """Get a SQLAlchemy engine with connection pooling.

    Returns:
        SQLAlchemy engine instance.
    """
    global _engine
    if _engine is None:
        settings = get_settings()

        db_config = None

        # Preferred: flat settings (Settings.db_url, etc.)
        if hasattr(settings, "db_url"):
            db_config = {
                "url": settings.db_url,
                "pool_size": getattr(settings, "db_pool_size", 10),
                "pool_timeout": getattr(settings, "db_pool_timeout", 30),
                "pool_recycle": getattr(settings, "db_pool_recycle", 3600),
                "echo": getattr(settings, "db_echo", False),
                "pool_pre_ping": True,
                "poolclass": QueuePool,
            }
        # Legacy nested: settings.db.url
        elif hasattr(settings, "db") and getattr(settings.db, "url", None):
            db = settings.db
            db_config = {
                "url": db.url,
                "pool_size": getattr(db, "pool_size", 10),
                "pool_timeout": getattr(db, "pool_timeout", 30),
                "pool_recycle": getattr(db, "pool_recycle", 3600),
                "echo": getattr(db, "echo_sql", False),
                "pool_pre_ping": True,
                "poolclass": QueuePool,
            }
        # Old-style UPPERCASE envs
        else:
            warnings.warn(
                "Using deprecated database configuration. Update to flat Settings.db_url.",
                DeprecationWarning,
                stacklevel=2,
            )
            db_config = {
                "url": getattr(settings, "DB_URL", "sqlite:///./dev.db"),
                "pool_size": getattr(settings, "DB_POOL_SIZE", 10),
                "pool_timeout": getattr(settings, "DB_POOL_TIMEOUT", 30),
                "pool_recycle": getattr(settings, "DB_POOL_RECYCLE", 3600),
                "echo": getattr(settings, "DB_ECHO", False),
                "pool_pre_ping": True,
                "poolclass": QueuePool,
            }

        _engine = create_engine(**db_config)

    return _engine


def get_session_factory() -> sessionmaker:
    """Get a SQLAlchemy session factory.

    Returns:
        SQLAlchemy sessionmaker instance.
    """
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get a database session for dependency injection.

    Yields:
        SQLAlchemy Session: A database session that should be used within a context manager.

    Example:
        ```python
        # In FastAPI route
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
        ```
    """
    Session = get_session_factory()
    db = Session()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> dict[str, bool | str]:
    """Check if the database is accessible.

    Returns:
        dict: A dictionary containing the status of the database connection.
            - ok (bool): True if the database is accessible, False otherwise.
            - error (str, optional): Error message if the connection failed.
    """
    try:
        with get_engine().connect() as conn:
            res = conn.execute(text("SELECT 1")).scalar()
            return {"ok": bool(res == 1)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Backward compatibility: expose SessionLocal alias expected by older code/tests
# This provides a sessionmaker instance identical to get_session_factory()
SessionLocal = get_session_factory()
