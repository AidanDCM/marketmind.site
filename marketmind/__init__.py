"""MarketMind Autopilot core package."""

from .adapters.shopify_adapter import build_product_draft
from .adapters.stripe_adapter import build_payment_link_payload
from .approvals import classify_action_risk, evaluate_approval, make_approval_record
from .experiment_rules import evaluate_experiment
from .importers import import_ad_report_csv, import_orders_csv, import_products_csv
from .math_engine import calculate_unit_economics
from .reports import generate_daily_report
from .runner import (
    RunResult,
    hydrate_snapshots,
    record_snapshot,
    run_daily_cycle,
    scale_approval_id,
)
from .schemas import (
    AnalyticsEvent,
    ApprovalRecord,
    ApprovalStatus,
    AssumptionRecord,
    AssumptionStatus,
    BundleItem,
    Channel,
    ChannelRecommendation,
    CriterionScore,
    DailyMetrics,
    DailyReport,
    ExperimentRuling,
    ExperimentRulingResult,
    ExperimentSnapshot,
    FaqItem,
    ImportResult,
    ImportRow,
    ImportRowStatus,
    NicheCandidate,
    OfferContext,
    OfferSpec,
    PaymentLinkPayload,
    ProductCandidate,
    ProductCostInput,
    ProductDraftPayload,
    RecommendedAction,
    RiskLevel,
    ScoreResult,
    ScoreVerdict,
    ShopifyVariant,
    UnitEconomicsResult,
)
from .scoring import (
    classify_assumption,
    recommend_channel,
    score_niche,
    score_product,
)
from .spec_generator import generate_offer_spec

__all__ = [
    # Slice 1: commerce math
    "ProductCostInput",
    "RecommendedAction",
    "UnitEconomicsResult",
    "calculate_unit_economics",
    # Slice 2: scoring
    "AssumptionRecord",
    "AssumptionStatus",
    "Channel",
    "ChannelRecommendation",
    "CriterionScore",
    "NicheCandidate",
    "ProductCandidate",
    "ScoreResult",
    "ScoreVerdict",
    "classify_assumption",
    "recommend_channel",
    "score_niche",
    "score_product",
    # Slice 4: experiment rules
    "ExperimentRuling",
    "ExperimentRulingResult",
    "ExperimentSnapshot",
    "evaluate_experiment",
    # Slice 5: offer spec generator
    "AnalyticsEvent",
    "BundleItem",
    "FaqItem",
    "OfferContext",
    "OfferSpec",
    "generate_offer_spec",
    # Slice 6: approval queue
    "ApprovalRecord",
    "ApprovalStatus",
    "RiskLevel",
    "classify_action_risk",
    "evaluate_approval",
    "make_approval_record",
    # Slice 7: CSV import
    "ImportResult",
    "ImportRow",
    "ImportRowStatus",
    "import_ad_report_csv",
    "import_orders_csv",
    "import_products_csv",
    # Slice 8: daily report
    "DailyMetrics",
    "DailyReport",
    "generate_daily_report",
    # Slice 18: experiment-runner loop
    "RunResult",
    "hydrate_snapshots",
    "record_snapshot",
    "run_daily_cycle",
    "scale_approval_id",
    # Slice 9: Stripe adapter
    "PaymentLinkPayload",
    "build_payment_link_payload",
    # Slice 10: Shopify adapter
    "ProductDraftPayload",
    "ShopifyVariant",
    "build_product_draft",
]
