"""Database models package.

This package contains all database models for the MarketMind application.
"""

# Import and set up relationships after all models are loaded
from . import relationships
from .address import Address
from .base import Base, BaseModel, ScopedSession, SessionLocal, get_db, init_db
from .category import Category
from .channel_listing import ChannelListing
from .compliance import (
    CarrierMapping,
    CompliancePack,
    ComplianceViolation,
    ErasureJob,
    ListingComplianceState,
    ListingSnapshot,
    MAPCatalog,
    PrivacyRequest,
    PurchaseOrderEvidence,
    RestrictedCategory,
    RestrictedTerm,
    SupplierWhitelist,
    TaxAttestation,
)
from .customer import Customer
from .customer_support import (
    ChatbotInteraction,
    CustomerQuery,
    QueryPriority,
    QuerySource,
    QueryStatus,
)
from .decision import DecisionLog, KPIEvent
from .governance import (
    APIContract,
    ChaosExperiment,
    GovernanceDecision,
    Incident,
    KPIThreshold,
    PolicyRule,
    ReleaseRollout,
    RiskEvent,
    SecurityFinding,
    SLOBudget,
)
from .learning import (
    BenchmarkRun,
    DriftReport,
    FeatureSnapshot,
    ModelMetric,
    ModelVersion,
    RolloutState,
)
from .marketing import (
    AttributionEvent,
    BundleResult,
    BundleTrial,
    Campaign,
    CampaignAsset,
    CustomerCohort,
    CustomerJourney,
    Experiment,
    ExperimentResult,
    ExperimentVariant,
)
from .order import FulfillmentStatus, Order, OrderItem, OrderStatus, PaymentStatus
from .pricing import PricingExperiment, PricingSnapshot, PricingSource, PricingTier

# Import all models first
from .product import Product
from .product_attribute import ProductAttribute
from .product_category import product_categories
from .product_image import ProductImage
from .product_review import ProductReview
from .profit import ProfitModuleLog
from .supplier import Supplier
from .user import User

relationships.setup_relationships()

# Make models available at the package level
__all__ = [
    "Base",
    "BaseModel",
    "SessionLocal",
    "ScopedSession",
    "get_db",
    "init_db",
    "Product",
    "Category",
    "Customer",
    "Address",
    "Order",
    "OrderItem",
    "OrderStatus",
    "PaymentStatus",
    "FulfillmentStatus",
    "Supplier",
    "CustomerQuery",
    "ChatbotInteraction",
    "QueryStatus",
    "QueryPriority",
    "QuerySource",
    "PricingSnapshot",
    "PricingExperiment",
    "PricingSource",
    "PricingTier",
    "ProfitModuleLog",
    "ProductImage",
    "ProductAttribute",
    "ProductReview",
    "ChannelListing",
    "product_categories",
    "User",
    "DecisionLog",
    "KPIEvent",
    "PolicyRule",
    "GovernanceDecision",
    "RiskEvent",
    "Incident",
    "APIContract",
    "ReleaseRollout",
    "ChaosExperiment",
    "KPIThreshold",
    "SLOBudget",
    "SecurityFinding",
    "CompliancePack",
    "RestrictedTerm",
    "RestrictedCategory",
    "CarrierMapping",
    "MAPCatalog",
    "ListingComplianceState",
    "ComplianceViolation",
    "PrivacyRequest",
    "ErasureJob",
    "TaxAttestation",
    "PurchaseOrderEvidence",
    "SupplierWhitelist",
    "ListingSnapshot",
    "Campaign",
    "CampaignAsset",
    "Experiment",
    "ExperimentResult",
    "CustomerJourney",
    "AttributionEvent",
    "ExperimentVariant",
    "BundleTrial",
    "BundleResult",
    "CustomerCohort",
    "FeatureSnapshot",
    "ModelVersion",
    "ModelMetric",
    "DriftReport",
    "BenchmarkRun",
    "RolloutState",
]
