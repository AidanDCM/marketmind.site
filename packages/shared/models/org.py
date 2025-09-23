"""
Organization and Brain models for multi-tenancy.
"""

from enum import Enum
from typing import List, Optional

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import GUID, Base


class OrgStatus(str, Enum):
    """Organization status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class BillingPlan(str, Enum):
    """Billing plan types."""

    FREE = "free"
    STARTER = "starter"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"


class Org(Base):
    """Organization model representing a customer account."""

    __tablename__ = "org"

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[OrgStatus] = mapped_column(
        SQLEnum(OrgStatus, name="org_status"), default=OrgStatus.TRIAL, nullable=False
    )
    billing_plan: Mapped[BillingPlan] = mapped_column(
        SQLEnum(BillingPlan, name="billing_plan"), default=BillingPlan.FREE, nullable=False
    )

    # Relationships
    brains: Mapped[List["Brain"]] = relationship(
        "Brain", back_populates="org", cascade="all, delete-orphan", lazy="selectin"
    )

    # Constraints
    __table_args__ = (
        Index(
            "idx_org_name", "name", postgresql_using="gin", postgresql_ops={"name": "gin_trgm_ops"}
        ),
    )


class BrainStatus(str, Enum):
    """Brain status."""

    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"


class Brain(Base):
    """Brain model representing a focused business niche within an organization."""

    __tablename__ = "brain"

    # Core fields
    org_id: Mapped[GUID] = mapped_column(
        GUID(), ForeignKey("org.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    niche: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Primary business niche"
    )
    subniche: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Optional sub-niche for more specific categorization"
    )
    status: Mapped[BrainStatus] = mapped_column(
        SQLEnum(BrainStatus, name="brain_status"), default=BrainStatus.DRAFT, nullable=False
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="JSON configuration for this brain",
    )

    # Relationships
    org: Mapped[Org] = relationship("Org", back_populates="brains", lazy="joined")

    # Constraints
    __table_args__ = (
        # Ensure unique niche/subniche per org
        Index(
            "uq_brain_org_niche",
            "org_id",
            "niche",
            "subniche",
            unique=True,
            postgresql_where=(status != BrainStatus.ARCHIVED),
        ),
        # Ensure at least one brain per org is active
        CheckConstraint(
            "(status != 'active' OR org_id IN ("
            "  SELECT org_id FROM brain WHERE status = 'active' GROUP BY org_id HAVING COUNT(*) = 1"
            "))",
            name="one_active_brain_per_org",
        ),
    )

    @property
    def full_niche_path(self) -> str:
        """Get the full niche path as 'niche/subniche'."""
        if self.subniche:
            return f"{self.niche}/{self.subniche}"
        return self.niche
