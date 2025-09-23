"""Helper functions for working with the Amazon SP-API.

This module provides high-level functions to interact with the Amazon SP-API
using the SpapiClient class. It handles common operations like fetching
product data, competitive pricing, and buy box information."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Union

from .spapi_client import SpapiClient, SpapiError

logger = logging.getLogger(__name__)


class ProductPrice(TypedDict, total=False):
    """Typed dictionary for product price information."""

    listing_price: float
    shipping: float
    landed_price: float
    is_buybox_winner: bool
    is_featured_offer: bool
    condition: str
    fulfillment_channel: str
    timestamp: datetime


def get_competitive_pricing(
    asins: Union[str, List[str]],
    region: Optional[str] = None,
    marketplace_id: Optional[str] = None,
    **client_kwargs,
) -> Dict[str, List[ProductPrice]]:
    """Get competitive pricing information for one or more ASINs.

    Args:
        asins: A single ASIN or list of ASINs to get pricing for
        region: Amazon region (default: from env or 'na')
        marketplace_id: Amazon Marketplace ID (default: from env)
        **client_kwargs: Additional arguments to pass to SpapiClient

    Returns:
        Dictionary mapping ASINs to lists of price offers

    Example:
        >>> prices = get_competitive_pricing(['B07K3SS94V', 'B07K3SS94V'])
        >>> prices['B07K3SS94V'][0]['landed_price']
        19.99
    """
    if isinstance(asins, str):
        asins = [asins]

    client = SpapiClient(region=region, **client_kwargs)

    try:
        # Fetch competitive pricing data
        pricing_data = client.get_competitive_pricing(asins)

        # Process the response
        result = {}
        for item in pricing_data.get("payload", []):
            asin = item.get("ASIN")
            if not asin:
                continue

            offers = []
            for offer in (
                item.get("Product", {}).get("CompetitivePricing", {}).get("CompetitivePrices", [])
            ):
                price_info = offer.get("Price", {})

                # Extract price components
                listing_price = float(price_info.get("ListingPrice", {}).get("Amount", 0))
                shipping = float(price_info.get("Shipping", {}).get("Amount", 0))

                offers.append(
                    {
                        "listing_price": listing_price,
                        "shipping": shipping,
                        "landed_price": listing_price + shipping,
                        "is_buybox_winner": offer.get("CompetitivePriceId", "").endswith(
                            "COMPETITIVE_PRICE"
                        ),
                        "is_featured_offer": offer.get("CompetitivePriceId", "").endswith(
                            "NEW_FEATURED_OFFER"
                        ),
                        "condition": offer.get("condition", ""),
                        "fulfillment_channel": offer.get("fulfillmentChannel", ""),
                        "timestamp": datetime.utcnow(),
                    }
                )

            result[asin] = offers

        return result

    except SpapiError as e:
        logger.error(f"Error fetching competitive pricing: {e}")
        raise


def get_buy_box_price(
    asin: str, region: Optional[str] = None, marketplace_id: Optional[str] = None, **client_kwargs
) -> Optional[float]:
    """Get the current buy box price for an ASIN.

    Args:
        asin: The ASIN to check
        region: Amazon region (default: from env or 'na')
        marketplace_id: Amazon Marketplace ID (default: from env)
        **client_kwargs: Additional arguments to pass to SpapiClient

    Returns:
        The buy box price as a float, or None if not available
    """
    try:
        pricing = get_competitive_pricing(asin, region, marketplace_id, **client_kwargs)
        offers = pricing.get(asin, [])

        # Find the buy box winner (if any)
        for offer in offers:
            if offer.get("is_buybox_winner", False):
                return offer.get("landed_price")

        # If no buy box winner, return the lowest price
        if offers:
            return min(offer.get("landed_price", float("inf")) for offer in offers)

    except Exception as e:
        logger.error(f"Error getting buy box price for {asin}: {e}")

    return None


def get_product_details(
    asin: str, region: Optional[str] = None, marketplace_id: Optional[str] = None, **client_kwargs
) -> Dict[str, Any]:
    """Get detailed product information for an ASIN.

    Args:
        asin: The ASIN to look up
        region: Amazon region (default: from env or 'na')
        marketplace_id: Amazon Marketplace ID (default: from env)
        **client_kwargs: Additional arguments to pass to SpapiClient

    Returns:
        Dictionary with product details
    """
    client = SpapiClient(region=region, **client_kwargs)

    try:
        # Get catalog item data
        catalog_data = client.get_catalog_item(asin)

        # Get competitive pricing
        pricing_data = get_competitive_pricing(asin, region, marketplace_id, **client_kwargs)

        # Combine the data
        result = {
            "asin": asin,
            "title": catalog_data.get("attributes", {}).get("item_name")
            or catalog_data.get("attributes", {}).get("title")
            or catalog_data.get("item_name")
            or catalog_data.get("title", ""),
            "brand": catalog_data.get("attributes", {}).get("brand")
            or catalog_data.get("brand", ""),
            "manufacturer": catalog_data.get("attributes", {}).get("manufacturer")
            or catalog_data.get("manufacturer", ""),
            "prices": pricing_data.get(asin, []),
            "buy_box_price": get_buy_box_price(asin, region, marketplace_id, **client_kwargs),
            "last_updated": datetime.utcnow().isoformat(),
            "raw_data": {"catalog": catalog_data, "pricing": pricing_data},
        }

        return result

    except SpapiError as e:
        logger.error(f"Error getting product details for {asin}: {e}")
        raise


def get_orders(
    created_after: datetime,
    created_before: Optional[datetime] = None,
    order_statuses: Optional[List[str]] = None,
    region: Optional[str] = None,
    **client_kwargs,
) -> List[Dict[str, Any]]:
    """Fetch orders from Amazon SP-API.

    Args:
        created_after: Fetch orders created after this datetime
        created_before: Fetch orders created before this datetime (optional)
        order_statuses: List of order statuses to include (default: all)
        region: Amazon region (default: from env or 'na')
        **client_kwargs: Additional arguments to pass to SpapiClient

    Returns:
        List of order dictionaries
    """
    # NOTE: In a full implementation, a client would be instantiated and used here.
    # client = SpapiClient(region=region, **client_kwargs)

    # Format dates as ISO 8601 strings
    params = {
        "CreatedAfter": created_after.isoformat(),
    }

    if created_before:
        params["CreatedBefore"] = created_before.isoformat()

    if order_statuses:
        params["OrderStatuses"] = order_statuses

    try:
        # This is a placeholder - the actual implementation would use the Orders API
        # orders = client.get_orders(**params)
        # return orders.get('payload', {}).get('Orders', [])
        return []

    except SpapiError as e:
        logger.error(f"Error fetching orders: {e}")
        raise
