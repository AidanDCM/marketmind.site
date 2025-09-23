from sp_api.api import ListingsItems, Orders, ProductPricing
from sp_api.base import Marketplaces


class AmazonClient:
    """Client for Amazon SP-API"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        aws_access_key: str,
        aws_secret_key: str,
        role_arn: str,
        marketplace_id=None,
    ):
        self.orders_api = Orders(
            refresh_token=refresh_token,
            lwa_app_id=client_id,
            lwa_client_secret=client_secret,
            aws_access_key=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            role_arn=role_arn,
            marketplace=marketplace_id or Marketplaces.US,
        )
        self.pricing_api = ProductPricing(
            refresh_token=refresh_token,
            lwa_app_id=client_id,
            lwa_client_secret=client_secret,
            aws_access_key=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            role_arn=role_arn,
            marketplace=marketplace_id or Marketplaces.US,
        )
        self.listings_api = ListingsItems(
            refresh_token=refresh_token,
            lwa_app_id=client_id,
            lwa_client_secret=client_secret,
            aws_access_key=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            role_arn=role_arn,
            marketplace=marketplace_id or Marketplaces.US,
        )

    def get_new_orders(self):
        """Fetch recent orders (stub implementation)"""
        # TODO: implement incremental order fetch
        return []

    def get_competitor_price(self, asin: str) -> float:
        """Fetch competitive pricing for a given ASIN"""
        try:
            # Fetch competitive pricing data from SP-API
            res = self.pricing_api.get_competitive_pricing_for_asin([asin])
            data = res.payload
            comp_prices = data.get("CompetitivePricing", [])
            if comp_prices:
                prices = comp_prices[0].get("CompetitivePrices", [])
                if prices:
                    price_info = prices[0].get("Price", {})
                    listing = price_info.get("ListingPrice", {}).get("Amount", 0.0)
                    shipping = price_info.get("Shipping", {}).get("Amount", 0.0)
                    return float(listing) + float(shipping)
        except Exception:
            raise
        return 0.0

    def update_listing_price(self, asin: str, price: float):
        """Update the listing price for an ASIN"""
        try:
            # Send price update via SP-API
            body = {"listingPrice": {"amount": price, "currencyCode": "USD"}}
            self.listings_api.patch_listings_item(asin, body)
        except Exception:
            raise
