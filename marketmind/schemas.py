"""Schemas for MarketMind commerce calculations.

These dataclasses intentionally avoid runtime dependencies in the first slice.
Later slices can replace or wrap them with Pydantic models if stronger validation
or JSON-schema generation becomes useful.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RecommendedAction(str, Enum):
    """Business-safe action labels emitted by the math engine."""

    REJECT = "reject"
    REVISE_OFFER = "revise_offer"
    ORGANIC_ONLY_TEST = "organic_only_test"
    PAID_TEST_REQUIRES_APPROVAL = "paid_test_requires_approval"
    CONTINUE_TEST = "continue_test"
    PAUSE_ADS = "pause_ads"
    KILL_PRODUCT = "kill_product"
    SCALE_REQUIRES_APPROVAL = "scale_requires_approval"


@dataclass(frozen=True)
class ProductCostInput:
    """Inputs needed to estimate first-order product economics.

    All money values are expressed in the same currency, usually USD.
    """

    product_name: str
    sale_price: float
    product_cost: float
    packaging_cost: float = 0.0
    shipping_cost: float = 0.0
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    refund_allowance: float = 0.0
    software_allocation: float = 0.0
    estimated_cac: float = 0.0

    def __post_init__(self) -> None:
        if not self.product_name.strip():
            raise ValueError("product_name is required")

        numeric_fields = {
            "sale_price": self.sale_price,
            "product_cost": self.product_cost,
            "packaging_cost": self.packaging_cost,
            "shipping_cost": self.shipping_cost,
            "platform_fee": self.platform_fee,
            "payment_fee": self.payment_fee,
            "refund_allowance": self.refund_allowance,
            "software_allocation": self.software_allocation,
            "estimated_cac": self.estimated_cac,
        }

        for field_name, value in numeric_fields.items():
            if value < 0:
                raise ValueError(f"{field_name} must be non-negative")

        if self.sale_price == 0:
            raise ValueError("sale_price must be greater than zero")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnitEconomicsResult:
    """Structured result returned by the commerce math engine."""

    product_name: str
    sale_price: float
    total_non_ad_cost: float
    gross_profit_before_ads: float
    break_even_cac: float
    safe_cac_low: float
    safe_cac_high: float
    estimated_cac: float
    estimated_contribution_profit: float
    gross_margin_before_ads: float
    contribution_margin_after_ads: float
    margin_status: str
    recommended_action: RecommendedAction
    risks: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["recommended_action"] = self.recommended_action.value
        data["risks"] = list(self.risks)
        return data


# ---------------------------------------------------------------------------
# Slice 2: scoring schemas (products, niches, assumptions, channels)
#
# Rating fields are normalized 0.0-1.0. To keep scoring explainable, fields
# named "*_risk" use the convention "higher = worse"; every other rating uses
# "higher = better". The scoring engine inverts the risk fields internally.
# ---------------------------------------------------------------------------


def _check_unit(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0")


class ScoreVerdict(str, Enum):
    """Overall verdict for a scored candidate."""

    PASS = "pass"          # good: clears the bar and has enough evidence
    REVIEW = "review"      # risky/unverified: needs a human look before spending
    REJECT = "reject"      # rejected: blocked or structurally too weak


class Channel(str, Enum):
    """Where an offer could be sold. Mirrors the ARCHITECTURE platform ladder."""

    STRIPE_PAYMENT_LINK = "stripe_payment_link"  # storefront-style validation page
    SHOPIFY = "shopify"                          # owned storefront
    EBAY = "ebay"                                # marketplace
    TIKTOK_SHOP = "tiktok_shop"                  # marketplace + content
    AMAZON_LATER = "amazon_later"                # marketplace, deferred (complex)
    DO_NOT_SELL = "do_not_sell"                  # blocked


class AssumptionStatus(str, Enum):
    """Evidence-backed status of an assumption in the ledger."""

    UNVERIFIED = "unverified"
    WEAK = "weak"
    SUPPORTED = "supported"
    VERIFIED = "verified"


@dataclass(frozen=True)
class ProductCandidate:
    """A product/offer idea to be scored. Money fields drive margin/shipping
    sub-scores numerically; the remaining 0-1 ratings are operator/research
    judgments."""

    product_name: str
    est_sale_price: float
    est_product_cost: float
    est_shipping_cost: float = 0.0
    competition: float = 0.5            # higher = more crowded = worse
    return_risk: float = 0.3            # higher = worse
    compliance_risk: float = 0.0        # higher = worse (regulated/unsafe)
    content_potential: float = 0.5      # higher = better (demo/UGC potential)
    repeat_purchase_potential: float = 0.3
    personal_fit: float = 0.5
    supplier_reliability: float = 0.5
    evidence_quality: float = 0.3       # how well-sourced the inputs are
    niche: str = ""

    def __post_init__(self) -> None:
        if not self.product_name.strip():
            raise ValueError("product_name is required")
        if self.est_sale_price <= 0:
            raise ValueError("est_sale_price must be greater than zero")
        for name in ("est_product_cost", "est_shipping_cost"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in (
            "competition", "return_risk", "compliance_risk", "content_potential",
            "repeat_purchase_potential", "personal_fit", "supplier_reliability",
            "evidence_quality",
        ):
            _check_unit(name, getattr(self, name))


@dataclass(frozen=True)
class NicheCandidate:
    """A niche/portfolio idea to be scored. All ratings are 0-1."""

    niche_name: str
    demand: float = 0.5
    competition: float = 0.5            # higher = worse
    margin_potential: float = 0.5
    content_potential: float = 0.5
    personal_fit: float = 0.5
    supplier_availability: float = 0.5
    repeat_purchase_potential: float = 0.3
    regulatory_risk: float = 0.0        # higher = worse
    evidence_quality: float = 0.3

    def __post_init__(self) -> None:
        if not self.niche_name.strip():
            raise ValueError("niche_name is required")
        for name in (
            "demand", "competition", "margin_potential", "content_potential",
            "personal_fit", "supplier_availability", "repeat_purchase_potential",
            "regulatory_risk", "evidence_quality",
        ):
            _check_unit(name, getattr(self, name))


@dataclass(frozen=True)
class AssumptionRecord:
    """A single entry in the assumption ledger. The bot must track guesses as
    guesses; unsourced claims can never be marked verified."""

    statement: str
    evidence_quality: float = 0.0       # 0-1, how strong the backing evidence is
    source: str = ""                    # citation/where the evidence came from
    impact: str = "medium"              # low | medium | high

    def __post_init__(self) -> None:
        if not self.statement.strip():
            raise ValueError("statement is required")
        _check_unit("evidence_quality", self.evidence_quality)
        if self.impact not in {"low", "medium", "high"}:
            raise ValueError("impact must be low, medium, or high")


@dataclass(frozen=True)
class CriterionScore:
    """One explainable line item in a score breakdown."""

    name: str
    raw: float       # 0-1 sub-score for this criterion
    weight: float    # weight applied in the weighted average
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChannelRecommendation:
    """Recommended sales channel plus an explanation."""

    channel: Channel
    strategy: str            # "marketplace_first" | "storefront_first" | "blocked"
    confidence: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["channel"] = self.channel.value
        return data


@dataclass(frozen=True)
class ScoreResult:
    """Explainable score for a candidate."""

    name: str
    overall_score: float                 # 0-1 weighted average
    verdict: ScoreVerdict
    confidence: float                    # capped by evidence quality
    criteria: tuple[CriterionScore, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    channel: ChannelRecommendation | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["verdict"] = self.verdict.value
        data["criteria"] = [c.to_dict() for c in self.criteria]
        data["risks"] = list(self.risks)
        data["channel"] = self.channel.to_dict() if self.channel else None
        return data
