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
