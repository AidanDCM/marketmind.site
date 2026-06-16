"""Explainable scoring engine for MarketMind Autopilot (Slice 2).

This module scores product and niche candidates, classifies assumptions, and
recommends a sales channel. It is pure computation: no external APIs, no
spending, no side effects. Every score ships with a per-criterion breakdown so
Aidan can see *why* the bot likes or rejects an idea, and missing evidence is
never treated as a verified fact.
"""

from __future__ import annotations

from .rules import (
    ASSUMPTION_SUPPORTED,
    ASSUMPTION_VERIFIED,
    COMPLIANCE_RISK_BLOCK,
    HIGH_SHIPPING_SHARE,
    MARGIN_SCORE_HIGH,
    MARGIN_SCORE_LOW,
    MIN_EVIDENCE_FOR_PASS,
    MIN_HEALTHY_GROSS_MARGIN,
    NICHE_SCORE_WEIGHTS,
    PRODUCT_SCORE_WEIGHTS,
    SCORE_PASS,
    SCORE_REJECT,
    SHIPPING_SHARE_BAD,
    SHIPPING_SHARE_GOOD,
    SUPPLIER_RELIABILITY_BLOCK,
)
from .schemas import (
    AssumptionRecord,
    AssumptionStatus,
    Channel,
    ChannelRecommendation,
    CriterionScore,
    NicheCandidate,
    ProductCandidate,
    ScoreResult,
    ScoreVerdict,
)

# Channel-decision tuning (kept local; these are routing heuristics, not money rules).
_CONTENT_HIGH = 0.60
_EVIDENCE_PROVEN = 0.50
_REPEAT_STICKY = 0.40
_CONTENT_LOW = 0.40
_IMPULSE_PRICE_MAX = 50.0

_MARKETPLACE = {Channel.EBAY, Channel.TIKTOK_SHOP, Channel.AMAZON_LATER}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _linear(value: float, low: float, high: float, *, invert: bool = False) -> float:
    """Map ``value`` onto 0-1. low->0 and high->1 (or the reverse if inverted)."""

    if high == low:
        return 0.0
    fraction = _clamp01((value - low) / (high - low))
    return 1.0 - fraction if invert else fraction


def _weighted_average(subscores: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    return sum(subscores[name] * weight for name, weight in weights.items()) / total_weight


def _gross_margin(product: ProductCandidate) -> float:
    gross = product.est_sale_price - product.est_product_cost - product.est_shipping_cost
    return gross / product.est_sale_price


def classify_assumption(assumption: AssumptionRecord) -> AssumptionStatus:
    """Classify an assumption from its evidence. Unsourced claims can never be
    verified, no matter how high the self-reported evidence score is."""

    if assumption.evidence_quality >= ASSUMPTION_VERIFIED and assumption.source.strip():
        return AssumptionStatus.VERIFIED
    if assumption.evidence_quality >= ASSUMPTION_SUPPORTED:
        return AssumptionStatus.SUPPORTED
    if assumption.evidence_quality > 0.0:
        return AssumptionStatus.WEAK
    return AssumptionStatus.UNVERIFIED


def recommend_channel(product: ProductCandidate) -> ChannelRecommendation:
    """Recommend a sales channel and whether to go marketplace-first or
    storefront-first. Mirrors the ARCHITECTURE platform ladder."""

    margin = _gross_margin(product)
    confidence = round(_clamp01(0.30 + 0.60 * product.evidence_quality), 2)

    if (
        product.compliance_risk >= COMPLIANCE_RISK_BLOCK
        or margin <= 0
        or product.supplier_reliability < SUPPLIER_RELIABILITY_BLOCK
    ):
        return ChannelRecommendation(
            channel=Channel.DO_NOT_SELL,
            strategy="blocked",
            confidence=confidence,
            reason="Blocked: compliance risk, non-positive margin, or unreliable supplier.",
        )

    # Brandable + proven + sticky -> build an owned storefront.
    if (
        product.content_potential >= _CONTENT_HIGH
        and product.evidence_quality >= _EVIDENCE_PROVEN
        and margin >= MIN_HEALTHY_GROSS_MARGIN
        and product.repeat_purchase_potential >= _REPEAT_STICKY
    ):
        return ChannelRecommendation(
            channel=Channel.SHOPIFY,
            strategy="storefront_first",
            confidence=confidence,
            reason=(
                "Brandable, proven, and repeat-friendly: "
                "graduate to an owned Shopify storefront."
            ),
        )

    # High content + impulse price -> content marketplace.
    if product.content_potential >= _CONTENT_HIGH and product.est_sale_price <= _IMPULSE_PRICE_MAX:
        return ChannelRecommendation(
            channel=Channel.TIKTOK_SHOP,
            strategy="marketplace_first",
            confidence=confidence,
            reason="High content potential at an impulse price point: test on TikTok Shop first.",
        )

    # Commodity / search-driven -> existing marketplace traffic.
    if product.content_potential < _CONTENT_LOW:
        return ChannelRecommendation(
            channel=Channel.EBAY,
            strategy="marketplace_first",
            confidence=confidence,
            reason="Low content potential / commodity: use existing eBay marketplace demand first.",
        )

    # Otherwise validate cheaply with a landing page + Stripe Payment Link.
    return ChannelRecommendation(
        channel=Channel.STRIPE_PAYMENT_LINK,
        strategy="storefront_first",
        confidence=confidence,
        reason=(
            "Unproven: validate demand with a landing page and "
            "Stripe Payment Link before scaling."
        ),
    )


def score_product(product: ProductCandidate) -> ScoreResult:
    """Score a product candidate with an explainable breakdown."""

    margin = _gross_margin(product)
    shipping_share = product.est_shipping_cost / product.est_sale_price

    subscores: dict[str, float] = {
        "margin": _linear(margin, MARGIN_SCORE_LOW, MARGIN_SCORE_HIGH),
        "shipping": _linear(shipping_share, SHIPPING_SHARE_GOOD, SHIPPING_SHARE_BAD, invert=True),
        "competition": 1.0 - product.competition,
        "return_risk": 1.0 - product.return_risk,
        "compliance_risk": 1.0 - product.compliance_risk,
        "supplier_reliability": product.supplier_reliability,
        "content_potential": product.content_potential,
        "repeat_purchase_potential": product.repeat_purchase_potential,
        "personal_fit": product.personal_fit,
        "evidence_quality": product.evidence_quality,
    }

    reasons = {
        "margin": f"gross margin before ads ~{margin:.0%}",
        "shipping": f"shipping is ~{shipping_share:.0%} of price",
        "competition": f"competition rated {product.competition:.2f} (higher is worse)",
        "return_risk": f"return risk rated {product.return_risk:.2f} (higher is worse)",
        "compliance_risk": f"compliance risk rated {product.compliance_risk:.2f} (higher is worse)",
        "supplier_reliability": f"supplier reliability rated {product.supplier_reliability:.2f}",
        "content_potential": f"content potential rated {product.content_potential:.2f}",
        "repeat_purchase_potential": (
            f"repeat purchase potential rated {product.repeat_purchase_potential:.2f}"
        ),
        "personal_fit": f"personal fit rated {product.personal_fit:.2f}",
        "evidence_quality": f"evidence quality rated {product.evidence_quality:.2f}",
    }

    criteria = tuple(
        CriterionScore(
            name=name,
            raw=round(subscores[name], 4),
            weight=weight,
            reason=reasons[name],
        )
        for name, weight in PRODUCT_SCORE_WEIGHTS.items()
    )

    overall = _weighted_average(subscores, PRODUCT_SCORE_WEIGHTS)

    risks: list[str] = []
    blocking = False
    if margin <= 0:
        risks.append("negative_or_zero_margin")
        blocking = True
    if product.compliance_risk >= COMPLIANCE_RISK_BLOCK:
        risks.append("compliance_risk_blocking")
        blocking = True
    if product.supplier_reliability < SUPPLIER_RELIABILITY_BLOCK:
        risks.append("supplier_unreliable")
        blocking = True
    if shipping_share > HIGH_SHIPPING_SHARE:
        risks.append("shipping_cost_too_high")
    if product.return_risk >= 0.60:
        risks.append("high_return_risk")
    if product.competition >= 0.80:
        risks.append("very_high_competition")
    if product.evidence_quality < MIN_EVIDENCE_FOR_PASS:
        risks.append("insufficient_evidence")

    channel = recommend_channel(product)

    if blocking or overall < SCORE_REJECT:
        verdict = ScoreVerdict.REJECT
    elif overall >= SCORE_PASS and product.evidence_quality >= MIN_EVIDENCE_FOR_PASS:
        verdict = ScoreVerdict.PASS
    else:
        verdict = ScoreVerdict.REVIEW

    # Confidence is capped by evidence quality so unverified ideas never look certain.
    confidence = round(min(overall, 0.20 + 0.80 * product.evidence_quality), 2)

    reason_summary = _product_reason(verdict, risks, overall)

    return ScoreResult(
        name=product.product_name,
        overall_score=round(overall, 4),
        verdict=verdict,
        confidence=confidence,
        criteria=criteria,
        risks=tuple(risks),
        reason_summary=reason_summary,
        channel=channel,
    )


def _product_reason(verdict: ScoreVerdict, risks: list[str], overall: float) -> str:
    if verdict == ScoreVerdict.REJECT:
        if "compliance_risk_blocking" in risks:
            return "Reject: compliance/safety risk is too high to sell."
        if "negative_or_zero_margin" in risks:
            return "Reject: the offer has no gross margin to work with."
        if "supplier_unreliable" in risks:
            return "Reject: supplier reliability is too low to trust fulfillment."
        return f"Reject: overall score {overall:.2f} is below the bar."
    if verdict == ScoreVerdict.PASS:
        return f"Pass: overall score {overall:.2f} clears the bar with adequate evidence."
    if "insufficient_evidence" in risks:
        return f"Review: score {overall:.2f} looks promising but evidence is too thin to commit."
    return f"Review: score {overall:.2f} is borderline or carries risks that need a human look."


def score_niche(niche: NicheCandidate) -> ScoreResult:
    """Score a niche candidate with an explainable breakdown (no channel)."""

    subscores: dict[str, float] = {
        "demand": niche.demand,
        "margin_potential": niche.margin_potential,
        "competition": 1.0 - niche.competition,
        "supplier_availability": niche.supplier_availability,
        "repeat_purchase_potential": niche.repeat_purchase_potential,
        "content_potential": niche.content_potential,
        "regulatory_risk": 1.0 - niche.regulatory_risk,
        "personal_fit": niche.personal_fit,
        "evidence_quality": niche.evidence_quality,
    }
    reasons = {
        "demand": f"demand rated {niche.demand:.2f}",
        "margin_potential": f"margin potential rated {niche.margin_potential:.2f}",
        "competition": f"competition rated {niche.competition:.2f} (higher is worse)",
        "supplier_availability": f"supplier availability rated {niche.supplier_availability:.2f}",
        "repeat_purchase_potential": (
            f"repeat purchase potential rated {niche.repeat_purchase_potential:.2f}"
        ),
        "content_potential": f"content potential rated {niche.content_potential:.2f}",
        "regulatory_risk": f"regulatory risk rated {niche.regulatory_risk:.2f} (higher is worse)",
        "personal_fit": f"personal fit rated {niche.personal_fit:.2f}",
        "evidence_quality": f"evidence quality rated {niche.evidence_quality:.2f}",
    }

    criteria = tuple(
        CriterionScore(
            name=name,
            raw=round(subscores[name], 4),
            weight=weight,
            reason=reasons[name],
        )
        for name, weight in NICHE_SCORE_WEIGHTS.items()
    )
    overall = _weighted_average(subscores, NICHE_SCORE_WEIGHTS)

    risks: list[str] = []
    if niche.regulatory_risk >= COMPLIANCE_RISK_BLOCK:
        risks.append("regulatory_risk_blocking")
    if niche.competition >= 0.80:
        risks.append("very_high_competition")
    if niche.evidence_quality < MIN_EVIDENCE_FOR_PASS:
        risks.append("insufficient_evidence")

    if "regulatory_risk_blocking" in risks or overall < SCORE_REJECT:
        verdict = ScoreVerdict.REJECT
    elif overall >= SCORE_PASS and niche.evidence_quality >= MIN_EVIDENCE_FOR_PASS:
        verdict = ScoreVerdict.PASS
    else:
        verdict = ScoreVerdict.REVIEW

    confidence = round(min(overall, 0.20 + 0.80 * niche.evidence_quality), 2)
    reason_summary = _product_reason(verdict, risks, overall)

    return ScoreResult(
        name=niche.niche_name,
        overall_score=round(overall, 4),
        verdict=verdict,
        confidence=confidence,
        criteria=criteria,
        risks=tuple(risks),
        reason_summary=reason_summary,
        channel=None,
    )
