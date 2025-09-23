"""Amazon SP-API Channel Adapter (Premade Implementation).

This module provides a pre-built implementation of the ChannelAdapter interface
for Amazon's Selling Partner API (SP-API). It wraps the existing AmazonClient
from the third_party directory to provide a consistent interface for MarketMind.
"""

from typing import Any, Dict, List, cast

from third_party.amazon_adapter.amazon import AmazonClient

from .base import ChannelAdapter


class AmazonPremade(ChannelAdapter):
    """Amazon SP-API Channel Adapter (Premade Implementation).

    This adapter wraps the existing AmazonClient to provide a consistent
    interface for MarketMind's channel integration system.
    """

    name = "amazon"

    def __init__(self, creds: Dict[str, str], region: str = "na"):
        """Initialize the Amazon SP-API adapter.

        Args:
            creds: Dictionary containing required credentials:
                - AMAZON_SP_CLIENT_ID
                - AMAZON_SP_CLIENT_SECRET
                - AMAZON_SP_REFRESH_TOKEN
                - AWS_ACCESS_KEY_ID
                - AWS_SECRET_ACCESS_KEY
                - AMAZON_ROLE_ARN (optional)
            region: Amazon region/marketplace (default: "na")
        """
        required_creds = [
            "AMAZON_SP_CLIENT_ID",
            "AMAZON_SP_CLIENT_SECRET",
            "AMAZON_SP_REFRESH_TOKEN",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ]

        missing = [k for k in required_creds if not creds.get(k)]
        if missing:
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")

        self.client = AmazonClient(
            client_id=creds["AMAZON_SP_CLIENT_ID"],
            client_secret=creds["AMAZON_SP_CLIENT_SECRET"],
            refresh_token=creds["AMAZON_SP_REFRESH_TOKEN"],
            aws_access_key=creds["AWS_ACCESS_KEY_ID"],
            aws_secret_key=creds["AWS_SECRET_ACCESS_KEY"],
            role_arn=creds.get("AMAZON_ROLE_ARN", ""),
            marketplace_id=region.upper(),
        )

    def create_listing(self, draft: Dict[str, Any]) -> str:
        """Create a new product listing on Amazon.

        Args:
            draft: Product data in Amazon's expected format

        Returns:
            The SKU of the created listing
        """
        # The AmazonClient doesn't have a direct create_listings_item method,
        # so we'll implement a basic version here
        try:
            # This is a simplified example - adapt to your actual API
            sku = draft.get("sku")
            if not sku:
                raise ValueError("Product SKU is required")

            # TODO: Implement actual listing creation using the SP-API client
            # This is a placeholder that would need to be adapted to your needs
            # listing_data = self.client.create_listings_item(draft)
            # return listing_data.get('sku', '')

            return cast(str, sku)
        except Exception as e:
            self._handle_error(f"Failed to create listing: {str(e)}")
            # Re-raise to make the control flow explicit for type checkers
            raise

    def update_listing(self, listing_id: str, patch: Dict[str, Any]) -> None:
        """Update an existing product listing.

        Args:
            listing_id: The ASIN or SKU of the listing to update
            patch: Dictionary of fields to update
        """
        try:
            # The AmazonClient has an update_listing_price method we can use
            if "price" in patch:
                self.client.update_listing_price(listing_id, patch["price"])

            # TODO: Handle other fields in the patch

        except Exception as e:
            self._handle_error(f"Failed to update listing {listing_id}: {str(e)}")

    def sync_offer(self, listing_id: str, offer_patch: Dict[str, Any]) -> None:
        """Update offer details like price, quantity, etc.

        Args:
            listing_id: The ASIN or SKU of the offer to update
            offer_patch: Dictionary of offer fields to update
        """
        try:
            # For Amazon, offer updates are similar to listing updates
            self.update_listing(listing_id, offer_patch)
        except Exception as e:
            self._handle_error(f"Failed to sync offer {listing_id}: {str(e)}")

    def fetch_orders(self, since_iso: str) -> List[Dict[str, Any]]:
        """Fetch orders from the channel.

        Args:
            since_iso: ISO 8601 timestamp to fetch orders since

        Returns:
            List of order dictionaries
        """
        try:
            # The AmazonClient has a get_new_orders method we can use
            return cast(List[Dict[str, Any]], self.client.get_new_orders())
        except Exception as e:
            self._handle_error(f"Failed to fetch orders: {str(e)}")
            return []

    def upload_tracking(self, channel_order_id: str, tracking: Dict[str, Any]) -> None:
        """Upload tracking information for an order.

        Args:
            channel_order_id: The order ID from the channel
            tracking: Dictionary containing tracking information
        """
        try:
            # The AmazonClient doesn't have a direct tracking upload method,
            # so we'll implement a basic version here
            # TODO: Implement actual tracking upload using the SP-API client
            # self.client.confirm_shipment(channel_order_id, tracking)
            pass
        except Exception as e:
            self._handle_error(f"Failed to upload tracking for order {channel_order_id}: {str(e)}")

    def health(self) -> Dict[str, Any]:
        """Check the health of the channel connection.

        Returns:
            Dictionary with health status information
        """
        try:
            # Try a simple API call to check connectivity
            # The AmazonClient doesn't have a direct ping method, so we'll use get_new_orders
            self.client.get_new_orders()
            return {"ok": True, "message": "Connected to Amazon SP-API"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _handle_error(self, message: str) -> None:
        """Handle errors consistently.

        Args:
            message: Error message

        Raises:
            RuntimeError: Always raises with the provided message
        """
        # TODO: Add logging and error handling as needed
        raise RuntimeError(message)
