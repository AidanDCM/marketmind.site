"""Pricing-related background tasks for MarketMind.

This module contains Celery tasks for capturing pricing data, analyzing trends,
and optimizing product pricing.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from celery import shared_task
from sqlalchemy.orm import Session

from packages.database import ScopedSession
from packages.database.models import PricingSnapshot, PricingSource, Product

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_BATCH_SIZE = 100  # Number of products to process in a single batch
MIN_PRICE_CHANGE_PCT = 0.01  # 1% minimum price change to trigger notification


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def capture_pricing_snapshot(
    self,
    product_id: Optional[int] = None,
    source: str = PricingSource.API.value,
    batch_size: int = DEFAULT_BATCH_SIZE,
    **kwargs,
) -> Dict:
    """Capture pricing snapshot for a product or batch of products.

    Args:
        product_id: ID of the product to capture pricing for. If None, processes a batch.
        source: Source of the pricing data (e.g., 'amazon', 'walmart', 'api')
        batch_size: Number of products to process in a batch (if product_id is None)
        **kwargs: Additional parameters for the pricing capture

    Returns:
        Dictionary with results of the operation
    """
    db = ScopedSession()
    try:
        if product_id:
            # Capture pricing for a single product
            result = _capture_single_product_pricing(db, product_id, source, **kwargs)
            return {"status": "success", "processed": 1, "details": [result]}
        else:
            # Capture pricing for a batch of products
            results = _capture_batch_pricing(db, source, batch_size, **kwargs)
            return {"status": "success", "processed": len(results), "details": results}
    except Exception as e:
        logger.error(f"Error capturing pricing snapshot: {str(e)}")
        # Retry the task with exponential backoff
        raise self.retry(exc=e, countdown=60 * self.request.retries) from e
    finally:
        db.close()


def _capture_single_product_pricing(db: Session, product_id: int, source: str, **kwargs) -> Dict:
    """Capture pricing data for a single product.

    Args:
        db: Database session
        product_id: ID of the product to capture pricing for
        source: Source of the pricing data
        **kwargs: Additional parameters for the pricing capture

    Returns:
        Dictionary with the results of the operation
    """
    # Get the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"status": "error", "message": f"Product {product_id} not found"}

    # Get the current price (this would be replaced with actual API calls in production)
    current_price = _get_current_price_from_source(product, source, **kwargs)

    if current_price is None:
        return {
            "status": "error",
            "message": f"Failed to get price for product {product_id} from {source}",
        }

    # Check if the price has changed significantly from the last snapshot
    last_snapshot = (
        db.query(PricingSnapshot)
        .filter(PricingSnapshot.product_id == product_id)
        .filter(PricingSnapshot.source == source)
        .order_by(PricingSnapshot.captured_at.desc())
        .first()
    )

    price_changed = True
    if last_snapshot:
        price_diff_pct = abs(
            (current_price["sale_price"] - last_snapshot.sale_price) / last_snapshot.sale_price
        )
        price_changed = price_diff_pct >= MIN_PRICE_CHANGE_PCT

    # Create a new snapshot if the price changed or if we don't have a recent snapshot
    if price_changed or not last_snapshot or not _has_recent_snapshot(last_snapshot):
        snapshot = PricingSnapshot(
            product_id=product_id,
            source=source,
            base_price=current_price["base_price"],
            sale_price=current_price["sale_price"],
            currency=current_price.get("currency", "USD"),
            is_on_sale=current_price.get("is_on_sale", 0),
            in_stock=current_price.get("in_stock", 1),
            stock_quantity=current_price.get("stock_quantity"),
            free_shipping=current_price.get("free_shipping", 0),
            shipping_cost=current_price.get("shipping_cost", 0),
            competitor_name=current_price.get("competitor_name"),
            competitor_url=current_price.get("competitor_url"),
            notes=f"Automated pricing snapshot from {source}",
            metadata=current_price.get("metadata", {}),
            valid_until=datetime.utcnow() + timedelta(days=1),  # Default to 1 day validity
        )

        db.add(snapshot)
        db.commit()

        # Log the price change if applicable
        if last_snapshot and price_changed:
            logger.info(
                f"Price changed for product {product_id} ({product.name}): "
                f"{last_snapshot.sale_price} -> {current_price['sale_price']} {current_price.get('currency', 'USD')}"
            )

            # In a real app, you might want to trigger notifications or other actions here
            # e.g., _notify_price_change(product, last_snapshot, snapshot)

        return {
            "status": "success",
            "product_id": product_id,
            "price_changed": price_changed,
            "new_price": (
                float(current_price["sale_price"]) if current_price["sale_price"] else None
            ),
            "previous_price": float(last_snapshot.sale_price) if last_snapshot else None,
            "snapshot_id": snapshot.id,
        }
    else:
        return {
            "status": "skipped",
            "product_id": product_id,
            "reason": "Price has not changed significantly",
            "current_price": (
                float(current_price["sale_price"]) if current_price["sale_price"] else None
            ),
        }


def _capture_batch_pricing(
    db: Session, source: str, batch_size: int = DEFAULT_BATCH_SIZE, **kwargs
) -> List[Dict]:
    """Capture pricing data for a batch of products.

    Args:
        db: Database session
        source: Source of the pricing data
        batch_size: Maximum number of products to process
        **kwargs: Additional parameters for the pricing capture

    Returns:
        List of results for each processed product
    """
    # Get products that haven't been checked recently
    recent_threshold = datetime.utcnow() - timedelta(hours=1)

    products = (
        db.query(Product)
        .filter(
            (Product.is_active == 1)
            & (
                ~Product.id.in_(
                    db.query(PricingSnapshot.product_id)
                    .filter(PricingSnapshot.source == source)
                    .filter(PricingSnapshot.captured_at >= recent_threshold)
                )
            )
        )
        .limit(batch_size)
        .all()
    )

    results = []
    for product in products:
        try:
            result = _capture_single_product_pricing(db, product.id, source, **kwargs)
            results.append(result)
        except Exception as e:
            logger.error(f"Error capturing pricing for product {product.id}: {str(e)}")
            results.append({"status": "error", "product_id": product.id, "message": str(e)})

    return results


def _get_current_price_from_source(product: Product, source: str, **kwargs) -> Optional[Dict]:
    """Get the current price for a product from the specified source.

    This is a placeholder that would be implemented to call actual APIs or scrapers.

    Args:
        product: The product to get pricing for
        source: Source of the pricing data
        **kwargs: Additional parameters for the pricing request

    Returns:
        Dictionary with pricing data, or None if the price couldn't be determined
    """
    # In a real implementation, this would call the appropriate API or scraper
    # based on the source. For now, we'll return a mock response.

    # Example implementation for demonstration purposes:
    if source == "amazon":
        # This would call the Amazon SP-API in a real implementation
        return {
            "base_price": Decimal("19.99"),
            "sale_price": Decimal("17.99"),
            "is_on_sale": 1,
            "in_stock": 1,
            "stock_quantity": 100,
            "free_shipping": 1,
            "shipping_cost": Decimal("0.00"),
            "currency": "USD",
            "metadata": {
                "source": "amazon",
                "product_url": f"https://www.amazon.com/dp/{product.sku}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    elif source == "api":
        # This would call your own API in a real implementation
        return {
            "base_price": product.price,
            "sale_price": product.sale_price or product.price,
            "is_on_sale": 1 if product.sale_price and product.sale_price < product.price else 0,
            "in_stock": 1 if product.stock_quantity > 0 else 0,
            "stock_quantity": product.stock_quantity,
            "free_shipping": 1,  # Assuming free shipping is available
            "shipping_cost": Decimal("0.00"),
            "currency": "USD",
            "metadata": {"source": "internal_api", "timestamp": datetime.utcnow().isoformat()},
        }
    else:
        # Default mock response
        return {
            "base_price": Decimal("24.99"),
            "sale_price": Decimal("24.99"),
            "is_on_sale": 0,
            "in_stock": 1,
            "stock_quantity": 50,
            "free_shipping": 0,
            "shipping_cost": Decimal("4.99"),
            "currency": "USD",
            "metadata": {"source": source, "timestamp": datetime.utcnow().isoformat()},
        }


def _has_recent_snapshot(snapshot: PricingSnapshot, hours: int = 24) -> bool:
    """Check if a snapshot was taken recently.

    Args:
        snapshot: The pricing snapshot to check
        hours: Number of hours to consider as "recent"

    Returns:
        True if the snapshot was taken within the specified hours, False otherwise
    """
    if not snapshot or not snapshot.captured_at:
        return False

    return (datetime.utcnow() - snapshot.captured_at) < timedelta(hours=hours)


# Scheduled tasks
@shared_task
def schedule_daily_pricing_snapshots() -> Dict:
    """Schedule daily pricing snapshots for all active products."""
    # In a real implementation, this would be scheduled to run daily
    # and would enqueue tasks for each product or batch of products
    from .pricing_tasks import capture_pricing_snapshot

    # Get all active product IDs
    db = ScopedSession()
    try:
        product_ids = [p[0] for p in db.query(Product.id).filter(Product.is_active == 1).all()]

        # Enqueue a task for each product
        for product_id in product_ids:
            capture_pricing_snapshot.delay(product_id=product_id, source="api")

        return {
            "status": "success",
            "message": f"Scheduled pricing snapshots for {len(product_ids)} products",
            "product_count": len(product_ids),
        }
    except Exception as e:
        logger.error(f"Error scheduling pricing snapshots: {str(e)}")
        return {"status": "error", "message": f"Failed to schedule pricing snapshots: {str(e)}"}
    finally:
        db.close()
