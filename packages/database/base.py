"""Base database module for MarketMind.

This module provides the base SQLAlchemy configuration and base model class
that all database models should inherit from.
"""

from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from sqlalchemy import Column, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base, declared_attr, scoped_session, sessionmaker
from sqlalchemy.orm.session import Session

# Type variable for model classes
T = TypeVar("T", bound="BaseModel")

# Create a thread-safe session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

# Create a scoped session factory for use in web applications
ScopedSession = scoped_session(SessionLocal)


# Base class for all models
class BaseModel:
    """Base model class that provides common functionality for all models.

    This class provides the following features:
    - Automatic table name generation (converts CamelCase to snake_case)
    - Common columns (id, created_at, updated_at)
    - Helper methods for CRUD operations
    """

    # These will be set by SQLAlchemy
    id: int
    created_at: datetime
    updated_at: datetime

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Converts CamelCase class names to snake_case table names.
        Example: 'UserProfile' -> 'user_profiles'
        """
        name = cls.__name__.replace("Model", "")
        return "".join(
            [
                (
                    f"_{c.lower()}"
                    if i > 0 and c.isupper() and name[i - 1].islower()
                    else (
                        f"_{c.lower()}"
                        if i > 0 and c.isupper() and i < len(name) - 1 and name[i + 1].islower()
                        else c.lower()
                    )
                )
                for i, c in enumerate(name)
            ]
        ).lstrip("_")

    # Common columns
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def create(cls, db: Session, **kwargs) -> "BaseModel":
        """Create a new record and save it to the database."""
        obj = cls(**kwargs)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @classmethod
    def get(cls, db: Session, id: int) -> Optional["BaseModel"]:
        """Get a record by ID."""
        return db.query(cls).filter(cls.id == id).first()

    def update(self, db: Session, **kwargs) -> None:
        """Update the record with the given values."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """Delete the record from the database."""
        db.delete(self)
        db.commit()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model instance to a dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


# Create the declarative base
Base = declarative_base(cls=BaseModel)


def init_db(database_url: str) -> None:
    """Initialize the database connection and create tables.

    Args:
        database_url: The database connection URL
    """
    engine = create_engine(database_url)
    SessionLocal.configure(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Get a database session.

    This function is intended to be used as a FastAPI dependency.
    It yields a database session and ensures it's properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
