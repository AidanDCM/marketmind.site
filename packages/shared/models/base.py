"""
Base model definitions and common utilities for SQLAlchemy models.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, UUID):
                return str(UUID(value).hex)
            else:
                return value.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return UUID(value) if not isinstance(value, UUID) else value


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    Provides common columns and functionality:
    - UUID primary key
    - created_at/updated_at timestamps
    - JSON type for all databases
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(GUID(), primary_key=True, default=uuid4, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self) -> str:
        """Representation of the model."""
        params = ", ".join(f"{k}={v!r}" for k, v in self.to_dict().items() if not k.startswith("_"))
        return f"<{self.__class__.__name__}({params})>"
