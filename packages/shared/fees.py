"""
Fee and tax calculation utilities for different channels.

This module provides standardized fee calculations and tax handling
across all marketplace channels and DTC platforms.
"""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

ChannelType = Literal["amazon", "ebay", "walmart", "shopify", "tiktok", "etsy"]
TaxModel = Literal["marketplace_collected", "seller_collected"]


class FeeCalculator:
    """Calculate marketplace fees and taxes for different channels."""

    # Default fee structures per channel (as percentages)
    DEFAULT_FEES = {
        "amazon": {
            "referral_fee": 15.0,  # Varies by category, 15% is common
            "fba_fee": 3.0,  # Estimated FBA fulfillment
            "closing_fee": 0.0,  # No longer charged
            "variable_closing_fee": 0.0,
            "payment_processing": 0.0,  # Included in referral fee
            "advertising_fee": 0.0,  # Optional, calculated separately
        },
        "ebay": {
            "final_value_fee": 12.9,  # Standard category
            "insertion_fee": 0.0,  # Free listings for most sellers
            "payment_processing": 2.9,  # PayPal/Managed Payments
            "international_fee": 1.65,  # For international sales
            "promoted_listings": 0.0,  # Optional
        },
        "walmart": {
            "referral_fee": 15.0,  # Category dependent
            "fulfillment_fee": 0.0,  # WFS if used
            "payment_processing": 0.0,  # Included
            "advertising_fee": 0.0,  # Optional
        },
        "shopify": {
            "transaction_fee": 2.9,  # + 30¢ per transaction
            "payment_processing": 0.3,  # Fixed fee in dollars
            "shopify_payments": 0.0,  # If using Shopify Payments
            "app_fees": 0.0,  # Third-party app costs
        },
        "tiktok": {
            "commission_fee": 5.0,  # TikTok Shop commission
            "payment_processing": 2.9,  # Standard processing
            "fulfillment_fee": 0.0,  # If using TikTok fulfillment
        },
        "etsy": {
            "transaction_fee": 6.5,  # Etsy transaction fee
            "payment_processing": 3.0,  # + 25¢ per transaction
            "listing_fee": 0.20,  # Per listing (in dollars)
            "advertising_fee": 0.0,  # Optional Etsy Ads
        },
    }

    # Tax collection models per channel
    TAX_MODELS = {
        "amazon": "marketplace_collected",
        "ebay": "marketplace_collected",
        "walmart": "marketplace_collected",
        "shopify": "seller_collected",
        "tiktok": "marketplace_collected",
        "etsy": "marketplace_collected",
    }

    def __init__(self, channel: ChannelType, custom_fees: Optional[Dict[str, float]] = None):
        """Initialize fee calculator for a specific channel.

        Args:
            channel: The marketplace/channel name
            custom_fees: Optional custom fee overrides
        """
        self.channel = channel
        self.fees = self.DEFAULT_FEES.get(channel, {}).copy()

        if custom_fees:
            self.fees.update(custom_fees)

    def calculate_fees(
        self,
        item_price: float,
        shipping_price: float = 0.0,
        quantity: int = 1,
        category: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Calculate all fees for an order.

        Args:
            item_price: Item price before fees
            shipping_price: Shipping amount charged to customer
            quantity: Number of items
            category: Product category (affects some fee rates)
            **kwargs: Additional channel-specific parameters

        Returns:
            Dict with fee breakdown and totals
        """
        total_sale = (item_price * quantity) + shipping_price
        fees_breakdown = {}

        if self.channel == "amazon":
            fees_breakdown = self._calculate_amazon_fees(
                item_price, shipping_price, quantity, category, **kwargs
            )
        elif self.channel == "ebay":
            fees_breakdown = self._calculate_ebay_fees(
                item_price, shipping_price, quantity, category, **kwargs
            )
        elif self.channel == "walmart":
            fees_breakdown = self._calculate_walmart_fees(
                item_price, shipping_price, quantity, category, **kwargs
            )
        elif self.channel == "shopify":
            fees_breakdown = self._calculate_shopify_fees(
                item_price, shipping_price, quantity, category, **kwargs
            )
        else:
            # Generic calculation for other channels
            fees_breakdown = self._calculate_generic_fees(
                item_price, shipping_price, quantity, category, **kwargs
            )

        # Calculate totals
        total_fees = sum(fees_breakdown.values())
        net_revenue = total_sale - total_fees

        return {
            "channel": self.channel,
            "gross_sale": round(total_sale, 2),
            "fees_breakdown": fees_breakdown,
            "total_fees": round(total_fees, 2),
            "net_revenue": round(net_revenue, 2),
            "fee_percentage": round((total_fees / total_sale * 100) if total_sale > 0 else 0, 2),
        }

    def _calculate_amazon_fees(
        self,
        item_price: float,
        shipping_price: float,
        quantity: int,
        category: Optional[str],
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate Amazon-specific fees."""

        # Referral fee (on item price only, not shipping)
        referral_fee = (item_price * quantity) * (self.fees["referral_fee"] / 100)

        # FBA fee (if using FBA)
        fba_fee = 0.0
        if kwargs.get("fulfillment_method") == "fba":
            # Simplified FBA fee calculation
            fba_fee = (item_price * quantity) * (self.fees["fba_fee"] / 100)

        return {
            "referral_fee": round(referral_fee, 2),
            "fba_fee": round(fba_fee, 2),
            "closing_fee": 0.0,  # Amazon no longer charges this
        }

    def _calculate_ebay_fees(
        self,
        item_price: float,
        shipping_price: float,
        quantity: int,
        category: Optional[str],
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate eBay-specific fees."""
        total_sale = (item_price * quantity) + shipping_price

        # Final value fee (on total sale including shipping)
        final_value_fee = total_sale * (self.fees["final_value_fee"] / 100)

        # Payment processing fee
        payment_fee = total_sale * (self.fees["payment_processing"] / 100)

        # International fee (if applicable)
        international_fee = 0.0
        if kwargs.get("international_sale"):
            international_fee = total_sale * (self.fees["international_fee"] / 100)

        return {
            "final_value_fee": round(final_value_fee, 2),
            "payment_processing": round(payment_fee, 2),
            "international_fee": round(international_fee, 2),
            "insertion_fee": 0.0,  # Usually free
        }

    def _calculate_walmart_fees(
        self,
        item_price: float,
        shipping_price: float,
        quantity: int,
        category: Optional[str],
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate Walmart-specific fees."""
        item_total = item_price * quantity

        # Referral fee (on item price only)
        referral_fee = item_total * (self.fees["referral_fee"] / 100)

        return {
            "referral_fee": round(referral_fee, 2),
            "fulfillment_fee": 0.0,  # WFS fees calculated separately if used
        }

    def _calculate_shopify_fees(
        self,
        item_price: float,
        shipping_price: float,
        quantity: int,
        category: Optional[str],
        **kwargs,
    ) -> Dict[str, float]:
        """Calculate Shopify-specific fees."""
        total_sale = (item_price * quantity) + shipping_price

        # Transaction fee (percentage + fixed)
        transaction_fee = (total_sale * (self.fees["transaction_fee"] / 100)) + self.fees[
            "payment_processing"
        ]

        return {
            "transaction_fee": round(transaction_fee, 2),
            "shopify_subscription": 0.0,  # Monthly fee, not per-transaction
            "app_fees": 0.0,  # Third-party apps
        }

    def _calculate_generic_fees(
        self,
        item_price: float,
        shipping_price: float,
        quantity: int,
        category: Optional[str],
        **kwargs,
    ) -> Dict[str, float]:
        """Generic fee calculation for other channels."""
        total_sale = (item_price * quantity) + shipping_price

        # Use the first fee type as primary
        primary_fee_key = list(self.fees.keys())[0] if self.fees else "platform_fee"
        primary_fee_rate = list(self.fees.values())[0] if self.fees else 10.0

        primary_fee = total_sale * (primary_fee_rate / 100)

        return {primary_fee_key: round(primary_fee, 2)}

    def get_tax_model(self) -> TaxModel:
        """Get the tax collection model for this channel."""
        return self.TAX_MODELS.get(self.channel, "seller_collected")

    def calculate_net_profit(
        self,
        item_price: float,
        cogs: float,
        shipping_cost: float = 0.0,
        shipping_price: float = 0.0,
        quantity: int = 1,
        return_reserve: float = 0.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Calculate net profit after all costs.

        Args:
            item_price: Sale price per item
            cogs: Cost of goods sold per item
            shipping_cost: Actual shipping cost to fulfill
            shipping_price: Shipping charged to customer
            quantity: Number of items
            return_reserve: Reserve for potential returns
            **kwargs: Additional parameters for fee calculation

        Returns:
            Dict with profit breakdown
        """
        # Calculate fees
        fee_result = self.calculate_fees(item_price, shipping_price, quantity, **kwargs)

        # Calculate costs
        total_cogs = cogs * quantity
        total_shipping_cost = shipping_cost

        # Calculate profit
        gross_profit = fee_result["net_revenue"] - total_cogs - total_shipping_cost
        net_profit = gross_profit - return_reserve

        # Calculate margins
        gross_sale = fee_result["gross_sale"]
        gross_margin = (gross_profit / gross_sale * 100) if gross_sale > 0 else 0
        net_margin = (net_profit / gross_sale * 100) if gross_sale > 0 else 0

        return {
            **fee_result,
            "cogs": round(total_cogs, 2),
            "shipping_cost": round(total_shipping_cost, 2),
            "return_reserve": round(return_reserve, 2),
            "gross_profit": round(gross_profit, 2),
            "net_profit": round(net_profit, 2),
            "gross_margin_pct": round(gross_margin, 2),
            "net_margin_pct": round(net_margin, 2),
            "calculated_at": datetime.utcnow().isoformat(),
        }


def get_fee_calculator(
    channel: ChannelType, custom_fees: Optional[Dict[str, float]] = None
) -> FeeCalculator:
    """Factory function to get a fee calculator for a channel."""
    return FeeCalculator(channel, custom_fees)


def calculate_order_financials(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate complete financial breakdown for an order.

    Args:
        order_data: Order data with channel, items, pricing, etc.

    Returns:
        Dict with complete financial breakdown
    """
    channel = order_data.get("channel", "amazon")
    calculator = get_fee_calculator(channel)

    # Extract order details
    items_total = order_data.get("items_total", 0.0)
    shipping_total = order_data.get("shipping_total", 0.0)
    tax_total = order_data.get("tax_total", 0.0)
    quantity = order_data.get("quantity", 1)

    # Get COGS and costs
    cogs = order_data.get("cogs", 0.0)
    shipping_cost = order_data.get("est_shipping_cost", 0.0)
    return_reserve = order_data.get("return_reserve", items_total * 0.02)  # 2% default

    # Calculate profit
    profit_result = calculator.calculate_net_profit(
        item_price=items_total / quantity,
        cogs=cogs / quantity,
        shipping_cost=shipping_cost,
        shipping_price=shipping_total,
        quantity=quantity,
        return_reserve=return_reserve,
        fulfillment_method=order_data.get("fulfillment_method"),
        category=order_data.get("category"),
        international_sale=order_data.get("international_sale", False),
    )

    # Add tax information
    profit_result.update(
        {
            "tax_total": tax_total,
            "tax_model": calculator.get_tax_model(),
            "order_id": order_data.get("order_id"),
            "channel": channel,
        }
    )

    return profit_result


# Utility functions for common calculations
def estimate_return_reserve(
    item_price: float, channel: ChannelType, category: Optional[str] = None
) -> float:
    """Estimate return reserve based on channel and category."""
    base_rates = {
        "amazon": 0.03,  # 3% average return rate
        "ebay": 0.02,  # 2% average
        "walmart": 0.025,  # 2.5% average
        "shopify": 0.015,  # 1.5% for DTC
        "tiktok": 0.04,  # 4% higher for social commerce
        "etsy": 0.01,  # 1% lower for handmade/unique items
    }

    # Category adjustments
    category_multipliers = {
        "electronics": 1.5,
        "clothing": 2.0,
        "shoes": 2.5,
        "jewelry": 0.8,
        "books": 0.5,
        "home": 1.2,
    }

    base_rate = base_rates.get(channel, 0.02)
    category_multiplier = category_multipliers.get(category.lower() if category else "", 1.0)

    return item_price * base_rate * category_multiplier


def get_tax_jurisdictions(ship_to_region: str, channel: ChannelType) -> Dict[str, Any]:
    """Get tax jurisdiction information for an order."""
    # Simplified tax jurisdiction logic
    # In production, this would integrate with TaxJar, Avalara, etc.

    tax_model = FeeCalculator.TAX_MODELS.get(channel, "seller_collected")

    if tax_model == "marketplace_collected":
        return {
            "tax_model": "marketplace_collected",
            "jurisdiction": ship_to_region,
            "seller_responsibility": False,
            "remittance_required": False,
        }
    else:
        # Seller-collected - need to determine nexus and rates
        return {
            "tax_model": "seller_collected",
            "jurisdiction": ship_to_region,
            "seller_responsibility": True,
            "remittance_required": True,
            "estimated_rate": 0.08,  # 8% placeholder
        }
