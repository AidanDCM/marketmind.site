"""MarketMind Autopilot core package."""

from .experiment_rules import evaluate_experiment
from .math_engine import calculate_unit_economics
from .schemas import (
    AssumptionRecord,
    AssumptionStatus,
    Channel,
    ChannelRecommendation,
    CriterionScore,
    ExperimentRuling,
    ExperimentRulingResult,
    ExperimentSnapshot,
    NicheCandidate,
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
]
