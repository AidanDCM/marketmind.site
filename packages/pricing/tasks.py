"""Background tasks for the pricing module."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from packages.database.models import PricingSource, Product
from packages.database.models.pricing import PricingSnapshot as DBPricingSnapshot

from .snapshot import PricingSnapshotConfig, SnapshotStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def capture_pricing_snapshot_task(
    db: Session, config: PricingSnapshotConfig, user_id: Optional[int] = None
) -> Tuple[int, SnapshotStatus]:
    """Background task to capture a pricing snapshot.

    Args:
        db: Database session
        config: Configuration for the snapshot
        user_id: Optional ID of the user who initiated the snapshot

    Returns:
        Tuple of (snapshot_id, status)
    """

    snapshot_id = 0  # In a real implementation, this would be a generated ID
    success_count = 0
    error_count = 0

    try:
        # Get the base query for products
        query = db.query(Product)
        if config.product_ids:
            query = query.filter(Product.id.in_(config.product_ids))

        total_products = query.count()
        logger.info(f"Starting pricing snapshot for {total_products} products")

        # Process products in batches
        for offset in range(0, total_products, config.batch_size):
            batch = query.offset(offset).limit(config.batch_size).all()

            for product in batch:
                try:
                    # Capture our own pricing
                    await _capture_product_pricing(
                        db=db,
                        product=product,
                        source=PricingSource.MANUAL,
                        source_id=None,
                        user_id=user_id,
                        force_refresh=config.force_refresh,
                    )
                    success_count += 1

                    # Capture competitor pricing if enabled
                    if config.include_competitors:
                        # In a real implementation, this would fetch from competitor APIs
                        # For now, we'll just log a message
                        logger.debug(
                            f"Skipping competitor pricing for product {product.id} "
                            "(not implemented)"
                        )

                    # Capture supplier pricing if enabled
                    if config.include_suppliers:
                        # In a real implementation, this would fetch from supplier APIs
                        # For now, we'll just log a message
                        logger.debug(
                            f"Skipping supplier pricing for product {product.id} "
                            "(not implemented)"
                        )

                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"Error capturing pricing for product {product.id}: {str(e)}", exc_info=True
                    )

            # Commit after each batch
            db.commit()

        # Determine final status
        status = SnapshotStatus.COMPLETED
        if error_count > 0:
            status = SnapshotStatus.PARTIAL if success_count > 0 else SnapshotStatus.FAILED

        logger.info(
            f"Pricing snapshot completed: {success_count} products processed, "
            f"{error_count} errors"
        )

        return snapshot_id, status

    except Exception as e:
        logger.error(f"Error in pricing snapshot task: {str(e)}", exc_info=True)
        db.rollback()
        return snapshot_id, SnapshotStatus.FAILED


async def _capture_product_pricing(
    db: Session,
    product: Product,
    source: PricingSource,
    source_id: Optional[str],
    user_id: Optional[int] = None,
    force_refresh: bool = False,
) -> DBPricingSnapshot:
    """Capture pricing for a single product.

    Args:
        db: Database session
        product: The product to capture pricing for
        source: Source of the pricing data
        source_id: Optional source ID
        user_id: Optional ID of the user initiating the capture
        force_refresh: Whether to force a refresh even if recently updated

    Returns:
        The created PricingSnapshot record
    """
    # Check if we already have a recent price for this product/source
    if not force_refresh:
        existing = (
            db.query(DBPricingSnapshot)
            .filter(
                DBPricingSnapshot.product_id == product.id,
                DBPricingSnapshot.source == source.value,
                DBPricingSnapshot.captured_at >= datetime.now(timezone.utc) - timedelta(hours=24),
            )
            .first()
        )

        if existing:
            logger.debug(
                f"Skipping {source.value} pricing for product {product.id}: "
                "recent price already exists"
            )
            return existing

    # Create a new pricing snapshot record
    snapshot = DBPricingSnapshot(
        product_id=product.id,
        source=source.value,
        base_price=float(product.price),
        sale_price=None,
        cost=(float(product.cost_price) if (product.cost_price is not None) else None),
        captured_at=datetime.now(timezone.utc),
        metadata_={"captured_by": user_id, "source": source.value},
    )

    db.add(snapshot)
    return snapshot
