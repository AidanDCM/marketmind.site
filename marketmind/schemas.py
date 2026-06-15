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
