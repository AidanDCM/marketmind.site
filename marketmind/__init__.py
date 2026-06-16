"""MarketMind Autopilot core package."""

from .experiment_rules import evaluate_experiment
from .math_engine import calculate_unit_economics
from .schemas import (
    AnalyticsEvent,
    AssumptionRecord,
    AssumptionStatus,
    BundleItem,
    Channel,
    ChannelRecommendation,
    CriterionScore,
    ExperimentRuling,
    ExperimentRulingResult,
    ExperimentSnapshot,
    FaqItem,
    NicheCandidate,
    OfferContext,
    OfferSpec,
    ProductCandidate,
    ProductCostInput,
    RecommendedAction,
    ScoreResult,
    ScoreVerdict,
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
]
