"""Tax calculation module for MarketMind.

This module provides functionality for calculating taxes on orders based on various
jurisdictions and tax rules.
"""

from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field


class TaxRate(BaseModel):
    """Represents a tax rate for a specific jurisdiction."""

    country_code: str = Field(
        ..., min_length=2, max_length=2, description="ISO 3166-1 alpha-2 country code"
    )
    state_code: Optional[str] = Field(
        None, min_length=2, max_length=3, description="State/region code"
    )
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    rate: Decimal = Field(..., ge=0, le=1, description="Tax rate as a decimal (e.g., 0.08 for 8%)")
    tax_name: str = Field(..., description="Name of the tax (e.g., 'GST', 'VAT', 'Sales Tax')")
    is_shipping_taxable: bool = Field(True, description="Whether shipping is taxable")


class TaxCalculator:
    """Handles tax calculations for orders based on location and product categories."""

    def __init__(self):
        # Default tax rates by country/state
        self.tax_rates: Dict[Tuple[str, Optional[str], Optional[str]], TaxRate] = {
            # US tax rates (simplified)
            ("US", "CA", None): TaxRate(
                country_code="US",
                state_code="CA",
                rate=Decimal("0.0725"),
                tax_name="California Sales Tax",
                is_shipping_taxable=True,
            ),
            ("US", "NY", None): TaxRate(
                country_code="US",
                state_code="NY",
                rate=Decimal("0.04"),
                tax_name="New York State Sales Tax",
                is_shipping_taxable=True,
            ),
            # EU VAT rates (simplified)
            ("DE", None, None): TaxRate(
                country_code="DE",
                rate=Decimal("0.19"),
                tax_name="German VAT",
                is_shipping_taxable=True,
            ),
            ("FR", None, None): TaxRate(
                country_code="FR",
                rate=Decimal("0.20"),
                tax_name="French TVA",
                is_shipping_taxable=True,
            ),
            # Default rate for other countries
            ("US", None, None): TaxRate(
                country_code="US",
                rate=Decimal("0.05"),
                tax_name="US Sales Tax",
                is_shipping_taxable=True,
            ),
            (None, None, None): TaxRate(
                country_code="XX", rate=Decimal("0.0"), tax_name="No Tax", is_shipping_taxable=False
            ),
        }

    def get_tax_rate(
        self, country_code: str, state_code: Optional[str] = None, postal_code: Optional[str] = None
    ) -> TaxRate:
        """Get the applicable tax rate for a location.

        Args:
            country_code: ISO 3166-1 alpha-2 country code
            state_code: State/region code (optional)
            postal_code: Postal/ZIP code (optional)

        Returns:
            The applicable TaxRate
        """
        # Try the most specific match first
        if country_code and state_code and postal_code:
            key = (country_code.upper(), state_code.upper(), postal_code.upper())
            if key in self.tax_rates:
                return self.tax_rates[key]

        # Try country and state
        if country_code and state_code:
            key = (country_code.upper(), state_code.upper(), None)
            if key in self.tax_rates:
                return self.tax_rates[key]

        # Try just country
        if country_code:
            key = (country_code.upper(), None, None)
            if key in self.tax_rates:
                return self.tax_rates[key]

        # Default to the most generic rate
        return self.tax_rates[(None, None, None)]

    def calculate_tax(
        self,
        subtotal: Decimal,
        country_code: str,
        state_code: Optional[str] = None,
        postal_code: Optional[str] = None,
        shipping_cost: Decimal = Decimal("0"),
        is_shipping_taxable: Optional[bool] = None,
    ) -> Dict[str, Union[Decimal, List[Dict[str, Union[str, Decimal]]]]]:
        """Calculate tax for an order.

        Args:
            subtotal: Order subtotal (before tax)
            country_code: ISO 3166-1 alpha-2 country code
            state_code: State/region code (optional)
            postal_code: Postal/ZIP code (optional)
            shipping_cost: Shipping cost (optional)
            is_shipping_taxable: Whether shipping is taxable (overrides tax rate setting)

        Returns:
            Dictionary with total tax and breakdown by rate
        """
        tax_rate = self.get_tax_rate(country_code, state_code, postal_code)

        # Determine if shipping is taxable
        shipping_taxable = (
            is_shipping_taxable if is_shipping_taxable is not None else tax_rate.is_shipping_taxable
        )

        # Calculate tax on subtotal
        subtotal_tax = subtotal * tax_rate.rate

        # Calculate tax on shipping if applicable
        shipping_tax = shipping_cost * tax_rate.rate if shipping_taxable else Decimal("0")

        total_tax = subtotal_tax + shipping_tax

        return {
            "total_tax": total_tax.quantize(Decimal("0.01")),
            "tax_breakdown": [
                {
                    "name": tax_rate.tax_name,
                    "rate": float(tax_rate.rate),
                    "subtotal_tax": subtotal_tax.quantize(Decimal("0.01")),
                    "shipping_tax": shipping_tax.quantize(Decimal("0.01")),
                    "country_code": tax_rate.country_code,
                    "state_code": tax_rate.state_code,
                }
            ],
        }

    # New Phase 8 API: marketplace vs seller-collected with provider seam
    def calculate_with_model(
        self,
        *,
        tax_model: Literal["marketplace_collected", "seller_collected"],
        subtotal: Decimal,
        shipping_cost: Decimal,
        buyer_region: Dict[str, Optional[str]],
        channel_reported_tax: Optional[Decimal] = None,
        provider: Literal["none", "taxjar", "avalara"] = "none",
        provider_ctx: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Phase 8 entrypoint that determines tax by model.

        - marketplace_collected: trust channel reported tax (if given) or compute 0; return summary row.
        - seller_collected: compute with fallback table or external provider seam.
        """
        country = (buyer_region or {}).get("country") or ""
        state = (buyer_region or {}).get("state") or None
        postal = (buyer_region or {}).get("postal_code") or None

        if tax_model == "marketplace_collected":
            total_tax = channel_reported_tax or Decimal("0")
            return {
                "tax_model": tax_model,
                "total_tax": Decimal(total_tax).quantize(Decimal("0.01")),
                "tax_breakdown": [
                    {
                        "name": "Marketplace-Collected Tax",
                        "rate": None,
                        "subtotal_tax": Decimal("0.00"),
                        "shipping_tax": Decimal("0.00"),
                        "country_code": country or None,
                        "state_code": state,
                    }
                ],
            }

        # seller_collected path
        if provider in ("taxjar", "avalara"):
            # Provider seam: in Phase 8 we keep provider-agnostic; return NotImplemented marker
            return {
                "tax_model": tax_model,
                "provider": provider,
                "total_tax": Decimal("0.00"),
                "tax_breakdown": [],
                "note": "external tax provider seam not implemented; using fallback",
            }

        # Fallback rules-based calculator
        result = self.calculate_tax(
            subtotal=subtotal,
            country_code=country,
            state_code=state,
            postal_code=postal,
            shipping_cost=shipping_cost,
        )
        result["tax_model"] = tax_model
        return result


# Global instance of the tax calculator
tax_calculator = TaxCalculator()


def get_tax_calculator() -> TaxCalculator:
    """Get the global tax calculator instance.

    Returns:
        The global TaxCalculator instance
    """
    return tax_calculator
