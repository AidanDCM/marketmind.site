"""Business rules for MarketMind product economics.

These rules are intentionally conservative. They are designed to prevent the bot
from scaling bad math.
"""

SAFE_CAC_LOW_MULTIPLIER = 0.50
SAFE_CAC_HIGH_MULTIPLIER = 0.70
MIN_HEALTHY_GROSS_MARGIN = 0.40
MIN_TESTABLE_GROSS_MARGIN = 0.25
HIGH_SHIPPING_SHARE = 0.25
HIGH_NON_AD_COST_SHARE = 0.75


def round_money(value: float) -> float:
    """Round currency-like values consistently for reports."""

    return round(value + 0.000000001, 2)


def margin_status(gross_margin_before_ads: float, contribution_margin_after_ads: float) -> str:
    """Return a simple margin classification."""

    if contribution_margin_after_ads < 0:
        return "losing_after_ads"
    if gross_margin_before_ads >= MIN_HEALTHY_GROSS_MARGIN:
        return "healthy"
    if gross_margin_before_ads >= MIN_TESTABLE_GROSS_MARGIN:
        return "thin"
    return "weak"


# ---------------------------------------------------------------------------
# Slice 2: scoring rules
#
# Weights are deliberately conservative: money math (margin/shipping) and risk
# dimensions carry the most weight, while "nice to have" signals carry less.
# Weights are normalized at runtime, so they need not sum to exactly 1.0.
# ---------------------------------------------------------------------------

PRODUCT_SCORE_WEIGHTS: dict[str, float] = {
    "margin": 0.22,
    "shipping": 0.10,
    "competition": 0.10,
    "return_risk": 0.10,
    "compliance_risk": 0.10,
    "supplier_reliability": 0.10,
    "content_potential": 0.08,
    "repeat_purchase_potential": 0.08,
    "personal_fit": 0.05,
    "evidence_quality": 0.07,
}

# Margin sub-score mapping: gross margin (before ads) at or below LOW maps to 0,
# at or above HIGH maps to 1, linear in between.
MARGIN_SCORE_LOW = 0.10
MARGIN_SCORE_HIGH = 0.50

# Shipping sub-score: shipping share of price at or below GOOD maps to 1, at or
# above BAD maps to 0.
SHIPPING_SHARE_GOOD = 0.05
SHIPPING_SHARE_BAD = 0.30

# Verdict thresholds on the overall 0-1 score.
SCORE_PASS = 0.62
SCORE_REJECT = 0.40

# A candidate is blocked outright when any of these hold.
COMPLIANCE_RISK_BLOCK = 0.70
SUPPLIER_RELIABILITY_BLOCK = 0.20

# Evidence below this cannot earn a PASS verdict (unverified ideas get REVIEW).
MIN_EVIDENCE_FOR_PASS = 0.40

NICHE_SCORE_WEIGHTS: dict[str, float] = {
    "demand": 0.20,
    "margin_potential": 0.18,
    "competition": 0.14,
    "supplier_availability": 0.12,
    "repeat_purchase_potential": 0.10,
    "content_potential": 0.08,
    "regulatory_risk": 0.08,
    "personal_fit": 0.05,
    "evidence_quality": 0.05,
}

# Assumption ledger thresholds.
ASSUMPTION_VERIFIED = 0.80
ASSUMPTION_SUPPORTED = 0.50
