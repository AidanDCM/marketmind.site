"""Customer support models for the MarketMind application."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

# Import Base from base.py to ensure all models use the same Base class
from .base import Base

if TYPE_CHECKING:
    from .customer import Customer
    from .order import Order
    from .user import User  # Assuming we'll have a User model for support agents


class QueryStatus(Enum):
    """Status of a customer query."""

    OPEN = "open"  # Query is newly created and unassigned
    IN_PROGRESS = "in_progress"  # Query is being worked on
    WAITING_CUSTOMER = "waiting_customer"  # Waiting for customer response
    RESOLVED = "resolved"  # Query has been resolved
    CLOSED = "closed"  # Query is closed (final state)
    REOPENED = "reopened"  # Query was reopened after being resolved/closed


class QueryPriority(Enum):
    """Priority of a customer query."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class QuerySource(Enum):
    """Source of a customer query."""

    EMAIL = "email"
    PHONE = "phone"
    CHAT = "chat"
    SOCIAL_MEDIA = "social_media"
    WEB = "web"  # alias used in tests
    WEB_FORM = "web_form"
    IN_PERSON = "in_person"
    OTHER = "other"


class CustomerQuery(Base):
    """Model representing customer support queries."""

    __tablename__ = "customer_queries"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    order_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("orders.id"), nullable=True
    )  # Optional: related order
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Support agent

    # Query details
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Alias to support tests using 'message'
    message = synonym("description")
    status: Mapped[QueryStatus] = mapped_column(
        SQLEnum(QueryStatus, values_callable=lambda x: [e.value for e in x]),
        default=QueryStatus.OPEN,
        nullable=False,
        index=True,
    )
    priority: Mapped[QueryPriority] = mapped_column(
        SQLEnum(QueryPriority, values_callable=lambda x: [e.value for e in x]),
        default=QueryPriority.MEDIUM,
        nullable=False,
    )
    source: Mapped[QuerySource] = mapped_column(
        SQLEnum(QuerySource, values_callable=lambda x: [e.value for e in x]),
        default=QuerySource.WEB_FORM,
        nullable=False,
    )

    # Resolution information
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Who resolved it

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON, nullable=True, default=list
    )  # For categorization
    meta: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )  # For additional data

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    first_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # When first response was sent
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )  # When query was closed

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="queries")
    order: Mapped[Optional["Order"]] = relationship("Order")
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])
    resolved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_id])
    interactions: Mapped[List["ChatbotInteraction"]] = relationship(
        "ChatbotInteraction",
        back_populates="query",
        order_by="ChatbotInteraction.created_at",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CustomerQuery(id={self.id}, status='{self.status.value}', customer_id={self.customer_id})>"

    @property
    def is_open(self) -> bool:
        """Check if the query is currently open."""
        return self.status in [
            QueryStatus.OPEN,
            QueryStatus.IN_PROGRESS,
            QueryStatus.WAITING_CUSTOMER,
            QueryStatus.REOPENED,
        ]

    @property
    def is_resolved(self) -> bool:
        """Check if the query has been resolved."""
        return self.status in [QueryStatus.RESOLVED, QueryStatus.CLOSED]

    @property
    def response_time(self) -> Optional[float]:
        """Calculate the response time in hours.

        Returns:
            Response time in hours, or None if not yet responded to
        """
        if not self.first_response_at or not self.created_at:
            return None
        return float((self.first_response_at - self.created_at).total_seconds() / 3600)

    @property
    def resolution_time(self) -> Optional[float]:
        """Calculate the resolution time in hours.

        Returns:
            Resolution time in hours, or None if not yet resolved
        """
        if not self.resolved_at or not self.created_at:
            return None
        return float((self.resolved_at - self.created_at).total_seconds() / 3600)

    def add_interaction(
        self, content: str, is_from_bot: bool = False, metadata: Optional[Dict] = None
    ) -> "ChatbotInteraction":
        """Add an interaction to this query.

        Args:
            content: The content of the interaction
            is_from_bot: Whether the interaction is from the bot
            metadata: Additional metadata for the interaction

        Returns:
            The created ChatbotInteraction
        """
        if self.interactions is None:
            self.interactions = []

        interaction = ChatbotInteraction(
            query=self, content=content, is_from_bot=is_from_bot, metadata=metadata or {}
        )

        # Update first response time if this is the first response from support
        if not is_from_bot and not self.first_response_at:
            self.first_response_at = datetime.utcnow()

        self.interactions.append(interaction)
        return interaction

    def update_status(self, new_status: QueryStatus, user_id: Optional[int] = None) -> None:
        """Update the status of the query.

        Args:
            new_status: The new status
            user_id: Optional user ID of who is making the change
        """
        self.status = new_status
        now = datetime.utcnow()

        if new_status == QueryStatus.RESOLVED:
            self.resolved_at = now
            self.resolved_by_id = user_id
        elif new_status == QueryStatus.CLOSED:
            self.closed_at = now
            # If it was resolved before, keep the original resolver
            if not self.resolved_at:
                self.resolved_at = now
                self.resolved_by_id = user_id

    def to_dict(self, include_interactions: bool = False) -> Dict[str, Any]:
        """Convert the query to a dictionary.

        Args:
            include_interactions: Whether to include the interactions

        Returns:
            Dictionary representation of the query
        """
        result = {
            "id": self.id,
            "customer_id": self.customer_id,
            "order_id": self.order_id,
            "assigned_to_id": self.assigned_to_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "priority": self.priority.value if self.priority else None,
            "source": self.source.value if self.source else None,
            "resolution": self.resolution,
            "is_open": self.is_open,
            "is_resolved": self.is_resolved,
            "response_time": self.response_time,
            "resolution_time": self.resolution_time,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "first_response_at": (
                self.first_response_at.isoformat() if self.first_response_at else None
            ),
        }

        if include_interactions and hasattr(self, "interactions"):
            result["interactions"] = [i.to_dict() for i in self.interactions]

        return result


class ChatbotInteraction(Base):
    """Model representing interactions with the chatbot for a customer query."""

    __tablename__ = "chatbot_interactions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    query_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customer_queries.id"), nullable=False
    )

    # Interaction content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_bot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Aliases/properties for test compatibility
    # 'message' alias for 'content'
    message = synonym("content")

    @property
    def sender_type(self) -> str:
        """Return sender type as expected by tests ("bot" or "customer")."""
        return "bot" if self.is_from_bot else "customer"

    @sender_type.setter
    def sender_type(self, value: str) -> None:
        """Allow setting via string sender type as used in tests."""
        self.is_from_bot = (value or "").lower() == "bot"

    # Metadata
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Detected intent
    confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )  # Confidence score of the intent
    meta: Mapped[Dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )  # For storing additional data

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    query: Mapped["CustomerQuery"] = relationship("CustomerQuery", back_populates="interactions")

    def __repr__(self) -> str:
        return f"<ChatbotInteraction(id={self.id}, query_id={self.query_id}, is_from_bot={self.is_from_bot})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the interaction to a dictionary."""
        return {
            "id": self.id,
            "query_id": self.query_id,
            "content": self.content,
            "is_from_bot": self.is_from_bot,
            "intent": self.intent,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.meta or {},
        }
