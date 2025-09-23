"""User model for the MarketMind application."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .customer_support import CustomerQuery


class User(Base):
    """Model representing a user in the system."""

    __tablename__ = "users"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User details
    username: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Profile information
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Metadata
    meta: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    assigned_queries: Mapped[List["CustomerQuery"]] = relationship(
        "CustomerQuery", foreign_keys="CustomerQuery.assigned_to_id", back_populates="assigned_to"
    )

    resolved_queries: Mapped[List["CustomerQuery"]] = relationship(
        "CustomerQuery", foreign_keys="CustomerQuery.resolved_by_id", back_populates="resolved_by"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        # username is Optional[str] at the ORM level; default to empty string when missing
        return self.username or ""
