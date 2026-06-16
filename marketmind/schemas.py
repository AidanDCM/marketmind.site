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


# ---------------------------------------------------------------------------
# Slice 4: experiment schemas
#
# ExperimentSnapshot captures what we've observed about a live experiment so far.
# ExperimentRulingis the decision the rule engine returns.
# ---------------------------------------------------------------------------


class ExperimentRuling(str, Enum):
    """Decision the experiment rule engine returns for a live test."""

    CONTINUE = "continue"
    PAUSE_ADS = "pause_ads"
    REVISE_OFFER = "revise_offer"
    KILL = "kill"
    SCALE_REQUIRES_APPROVAL = "scale_requires_approval"


@dataclass(frozen=True)
class ExperimentSnapshot:
    """Observed performance data for one experiment period.

    All rate fields are fractions (0.0-1.0). Money fields use the same currency
    as ProductCostInput. ``consecutive_losing_periods`` counts how many periods
    in a row the actual CAC has been above break-even.
    """

    experiment_id: str
    product_name: str
    break_even_cac: float                  # from the math engine
    qualified_visits: int = 0
    orders: int = 0
    total_ad_spend: float = 0.0
    total_revenue: float = 0.0
    refund_count: int = 0
    actual_shipping_cost: float = 0.0      # average per order
    planned_shipping_cost: float = 0.0     # from the original product input
    add_to_cart_count: int = 0
    consecutive_losing_periods: int = 0    # number of periods CAC > break-even
    budget_cap: float = 0.0                # 0 = not yet set (blocks spending)

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id is required")
        if not self.product_name.strip():
            raise ValueError("product_name is required")
        if self.break_even_cac < 0:
            raise ValueError("break_even_cac must be non-negative")
        for name in ("qualified_visits", "orders", "refund_count",
                     "add_to_cart_count", "consecutive_losing_periods"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("total_ad_spend", "total_revenue",
                     "actual_shipping_cost", "planned_shipping_cost", "budget_cap"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")

    # Derived metrics (computed from raw counters, never stored).

    @property
    def actual_cac(self) -> float:
        return self.total_ad_spend / self.orders if self.orders > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.orders / self.qualified_visits if self.qualified_visits > 0 else 0.0

    @property
    def add_to_cart_rate(self) -> float:
        return (
            self.add_to_cart_count / self.qualified_visits
            if self.qualified_visits > 0 else 0.0
        )

    @property
    def refund_rate(self) -> float:
        return self.refund_count / self.orders if self.orders > 0 else 0.0

    @property
    def shipping_overrun(self) -> float:
        """Fraction by which actual shipping exceeded plan (0.0 if on/under plan)."""
        if self.planned_shipping_cost <= 0:
            return 0.0
        overrun = (self.actual_shipping_cost - self.planned_shipping_cost)
        return max(0.0, overrun / self.planned_shipping_cost)


@dataclass(frozen=True)
class ExperimentRulingResult:
    """Structured result from the experiment rule engine."""

    experiment_id: str
    product_name: str
    ruling: ExperimentRuling
    risks: tuple[str, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    requires_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ruling"] = self.ruling.value
        data["risks"] = list(self.risks)
        return data


# ---------------------------------------------------------------------------
# Slice 5: offer and landing-page spec schemas
#
# All generation is template-based and deterministic. No LLM is called here.
# The safety_flags field names what must NOT appear on the page so Codex
# cannot accidentally build a page with fake urgency, fake reviews, etc.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OfferContext:
    """Operator-supplied context used to generate the offer spec.

    ``secondary_benefits`` and ``common_objections`` are tuples of short strings.
    All claims in the generated spec derive from these inputs — nothing is
    invented, and no results are guaranteed unless the operator explicitly
    provides verified evidence.
    """

    product_name: str
    sale_price: float
    key_benefit: str                          # single honest value proposition
    target_customer: str                      # who this is for
    secondary_benefits: tuple[str, ...] = field(default_factory=tuple)
    common_objections: tuple[str, ...] = field(default_factory=tuple)
    shipping_note: str = ""                   # e.g. "Ships in 5-7 business days"
    return_policy: str = ""                   # e.g. "30-day hassle-free returns"
    niche: str = ""

    def __post_init__(self) -> None:
        if not self.product_name.strip():
            raise ValueError("product_name is required")
        if not self.key_benefit.strip():
            raise ValueError("key_benefit is required")
        if not self.target_customer.strip():
            raise ValueError("target_customer is required")
        if self.sale_price <= 0:
            raise ValueError("sale_price must be greater than zero")


@dataclass(frozen=True)
class FaqItem:
    question: str
    answer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BundleItem:
    name: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalyticsEvent:
    name: str       # machine-readable event name, e.g. "page_view"
    trigger: str    # when it fires, e.g. "user lands on the page"
    properties: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["properties"] = list(self.properties)
        return data


@dataclass(frozen=True)
class OfferSpec:
    """Codex-ready spec for a product validation landing page.

    Every section is generated from operator-supplied inputs only. No invented
    claims, no guaranteed results, no fake urgency or scarcity.
    """

    product_name: str
    headline: str
    subheadline: str
    bundle_items: tuple[BundleItem, ...] = field(default_factory=tuple)
    faq: tuple[FaqItem, ...] = field(default_factory=tuple)
    cta_primary: str = ""
    cta_button_label: str = ""
    analytics_events: tuple[AnalyticsEvent, ...] = field(default_factory=tuple)
    trust_signals: tuple[str, ...] = field(default_factory=tuple)
    codex_build_notes: str = ""
    safety_flags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["bundle_items"] = [b.to_dict() for b in self.bundle_items]
        data["faq"] = [f.to_dict() for f in self.faq]
        data["analytics_events"] = [e.to_dict() for e in self.analytics_events]
        data["trust_signals"] = list(self.trust_signals)
        data["safety_flags"] = list(self.safety_flags)
        return data
