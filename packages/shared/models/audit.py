"""
Audit and event logging models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base


class AuditAction(str, Enum):
    """Types of audit actions."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    CONFIG_UPDATE = "config_update"
    PRICE_UPDATE = "price_update"
    INVENTORY_UPDATE = "inventory_update"
    ORDER_UPDATE = "order_update"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


class AuditLog(Base):
    """Audit log for tracking changes to entities."""

    __tablename__ = "audit_log"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("org.id", ondelete="CASCADE"),
        nullable=True,  # Allow system-wide logs
        index=True,
        comment="Organization ID (null for system events)",
    )
    brain_id: Mapped[Optional[GUID]] = mapped_column(
        GUID(),
        ForeignKey("brain.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Brain ID (if applicable)",
    )

    # Actor information
    actor_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        comment="Type of actor (system, user, api, etc.)",
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="ID of the actor (user ID, API key, etc.)"
    )
    actor_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Name of the actor (for display)"
    )

    # Action details
    action: Mapped[AuditAction] = mapped_column(
        String(30), nullable=False, index=True, comment="Type of action performed"
    )
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True, comment="Type of entity affected"
    )
    entity_id: Mapped[Optional[GUID]] = mapped_column(
        GUID(), nullable=True, index=True, comment="ID of the affected entity"
    )

    # Change details
    delta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, comment="JSON diff of changes (for updates)"
    )

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP address of the actor"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User agent string"
    )
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Correlation/request ID"
    )

    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
        comment="When the action occurred",
    )

    # Relationships
    org = relationship("Org", foreign_keys=[org_id])
    brain = relationship("Brain", foreign_keys=[brain_id])

    # Constraints
    __table_args__ = (
        # Index for common lookups
        Index("idx_audit_log_entity", "entity_type", "entity_id", "timestamp"),
        Index("idx_audit_log_actor", "actor_type", "actor_id", "timestamp"),
        # PostgreSQL-specific configuration
        {
            "postgresql_partition_by": "RANGE (timestamp)",
            # We'll handle the partition creation in a migration
        },
    )


class ConfigAudit(Base):
    """Audit trail for configuration changes."""

    __tablename__ = "config_audit"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("org.id", ondelete="CASCADE"),
        nullable=True,  # Allow system-wide config changes
        index=True,
    )

    # Actor information
    actor_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        comment="Type of actor (system, user, api, etc.)",
    )
    actor_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="ID of the actor (user ID, API key, etc.)"
    )

    # Change details
    key_path: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Dot-notation path of the changed config key"
    )
    scope: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="global",
        comment="Scope of the change (global, org:ID, brain:ID)",
    )
    old_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="SHA-256 hash of the old config value"
    )
    new_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="SHA-256 hash of the new config value"
    )

    # Metadata
    note: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Optional note about the change"
    )

    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
        comment="When the change occurred",
    )

    # Constraints
    __table_args__ = (
        # Index for common lookups
        Index("idx_config_audit_key_scope", "key_path", "scope"),
        Index("idx_config_audit_timestamp", "timestamp"),
    )


class InventoryEvent(Base):
    """Inventory change events for tracking stock levels over time."""

    __tablename__ = "inventory_event"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("org.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
        comment="Part of composite primary key for partitioning",
    )
    product_id: Mapped[GUID] = mapped_column(
        GUID(),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Product that was changed",
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Type of inventory event (ingest, adjust, sale, return, etc.)",
    )
    delta: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Change in quantity (positive or negative)"
    )

    # Context
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="system",
        comment="Source of the event (system, api, manual, etc.)",
    )
    reference_id: Mapped[Optional[GUID]] = mapped_column(
        GUID(), nullable=True, comment="Reference to related entity (order_id, return_id, etc.)"
    )
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Type of reference (order, return, adjustment, etc.)"
    )

    # Metadata
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",  # The actual column name in the database
        JSONB,
        default=dict,
        server_default="{}",
        comment="Additional event metadata",
    )

    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        index=True,
        comment="When the event occurred",
    )

    # Constraints
    __table_args__ = (
        # Index for common lookups
        Index("idx_inventory_event_product_timestamp", "product_id", "timestamp"),
        Index("idx_inventory_event_reference", "reference_type", "reference_id"),
        # Check constraints
        CheckConstraint("delta != 0", name="chk_inventory_event_non_zero_delta"),
        # PostgreSQL-specific configuration
        {
            "postgresql_partition_by": "RANGE (timestamp)",
            # We'll handle the partition creation in a migration
        },
    )
