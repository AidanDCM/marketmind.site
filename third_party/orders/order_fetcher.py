"""Order fetching and processing module for Amazon SP-API."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sp_api.api.orders.orders import Orders
from sp_api.base.marketplaces import Marketplaces
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class OrderFetcher:
    """Handles fetching and processing orders from Amazon SP-API."""

    def __init__(self, db_session: Session, config: dict):
        """Initialize the OrderFetcher.

        Args:
            db_session: SQLAlchemy database session
            config: Configuration dictionary with API credentials and settings
        """
        self.db = db_session
        self.config = config

        # Initialize Amazon SP-API client
        # Convert marketplace_id to Marketplaces enum
        marketplace = next(
            (m for m in Marketplaces if m.marketplace_id == config["marketplace_id"]),
            Marketplaces.US,  # Default to US if not found
        )

        self.orders_client = Orders(
            marketplace=marketplace,
            credentials={
                "refresh_token": config["refresh_token"],
                "lwa_app_id": config["client_id"],
                "lwa_client_secret": config["client_secret"],
                "aws_access_key": config["aws_access_key"],
                "aws_secret_key": config["aws_secret_key"],
                "role_arn": config.get("role_arn"),
            },
        )

    def fetch_orders(self, created_after: Optional[datetime] = None) -> Tuple[int, int]:
        """Fetch orders from Amazon SP-API and save them to the database.

        Args:
            created_after: Only fetch orders created after this datetime

        Returns:
            Tuple of (new_orders_count, total_processed)
        """
        if created_after is None:
            # Default to 1 hour ago if no specific time provided
            created_after = datetime.utcnow() - timedelta(hours=1)

        logger.info("Starting order sync", created_after=created_after.isoformat())

        try:
            # Create a sync status record with the correct fields
            sync_status = {
                "synced_to_inventory": False,
                "synced_to_accounting": False,
                "synced_to_shipping": False,
            }

            # Fetch orders from Amazon
            new_orders_count = 0
            next_token = None
            total_processed = 0

            while True:
                # Get orders from Amazon SP-API
                orders_response = self._get_orders_page(created_after, next_token)

                # Process the orders
                for order_data in orders_response.get("payload", {}).get("Orders", []):
                    order_added = self._process_order(order_data)
                    if order_added:
                        new_orders_count += 1
                    total_processed += 1

                # Check if there are more pages
                next_token = orders_response.get("payload", {}).get("NextToken")
                if not next_token:
                    break

                # Update sync status with pagination token
                if "last_sync_token" in sync_status:
                    sync_status["last_sync_token"] = next_token

            logger.info(
                f"Order sync completed. {new_orders_count} new orders out of {total_processed} total processed."
            )
            return new_orders_count, total_processed

        except Exception as e:
            logger.error(f"Error during order sync: {str(e)}", exc_info=True)
            raise

    def _get_orders_page(self, created_after: datetime, next_token: Optional[str] = None) -> dict:
        """Fetch a single page of orders from the SP-API."""
        params = {
            "CreatedAfter": created_after.isoformat(),
            "OrderStatuses": ["Unshipped", "PartiallyShipped"],
            "MarketplaceIds": [self.config["marketplace_id"]],
        }

        if next_token:
            params["NextToken"] = next_token

        try:
            if next_token:
                return self.orders_client.get_orders_next(next_token).payload
            else:
                return self.orders_client.get_orders(**params).payload
        except Exception as e:
            logger.error(f"Error fetching orders page: {str(e)}")
            raise

    def _process_order(self, order_data: dict) -> bool:
        """Process a single order and save it to the database."""
        try:
            # Extract tax information if available
            order_tax = order_data.get("OrderTotal", {}).get("Amount", "0")
            shipping_tax = order_data.get("ShippingPrice", {}).get("Amount", "0")

            # Create or update order in database
            # This is a simplified example - adapt to your actual database model
            order = {
                "order_id": order_data["AmazonOrderId"],
                "purchase_date": order_data["PurchaseDate"],
                "order_status": order_data["OrderStatus"],
                "total_amount": float(order_data.get("OrderTotal", {}).get("Amount", "0")),
                "item_tax": float(order_tax) if order_tax else 0.0,
                "shipping_tax": float(shipping_tax) if shipping_tax else 0.0,
                "shipping_address": order_data.get("ShippingAddress", {}).get("AddressLine1", ""),
                "shipping_city": order_data.get("ShippingAddress", {}).get("City", ""),
                "shipping_state": order_data.get("ShippingAddress", {}).get("StateOrRegion", ""),
                "shipping_zip": order_data.get("ShippingAddress", {}).get("PostalCode", ""),
                "shipping_country": order_data.get("ShippingAddress", {}).get("CountryCode", ""),
            }

            # TODO: Save to database using your ORM
            # Example: self.db.merge(Order(**order))
            # self.db.commit()

            logger.info(f"Processed order {order['order_id']}")
            return True

        except Exception as e:
            logger.error(
                f"Error processing order {order_data.get('AmazonOrderId', 'unknown')}: {str(e)}"
            )
            return False
