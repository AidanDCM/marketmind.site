"""Base database models for MarketMind.

This module contains the base SQLAlchemy model class that all database models should inherit from.
"""

from datetime import datetime
from typing import Any, Dict, TypeVar

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound="BaseModel")


class BaseModel:
    """Base model class that all database models should inherit from.

    Provides common columns (id, created_at, updated_at) and utility methods.
    """

    # This will be set by SQLAlchemy
    __abstract__ = True

    # Automatically set timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate __tablename__ automatically from class name."""
        return cls.__name__.lower() + "s"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}  # type: ignore

    @classmethod
    def get_by_id(cls, db: Session, id: Any) -> ModelType:
        """Get a model instance by its primary key."""
        return db.query(cls).filter(cls.id == id).first()  # type: ignore

    def save(self, db: Session) -> None:
        """Save the current instance to the database."""
        db.add(self)
        db.commit()
        db.refresh(self)

    def delete(self, db: Session) -> None:
        """Delete the current instance from the database."""
        db.delete(self)
        db.commit()


# Create a base class for all models to inherit from
Base = declarative_base(cls=BaseModel)
