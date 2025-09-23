"""Pricing Lab service for MarketMind.

This module provides functionality for analyzing pricing data, running experiments,
and optimizing product pricing strategies.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from packages.database import ScopedSession
from packages.database.models import (
    PricingExperiment,
    PricingSnapshot,
    Product,
)


class PricingLabService:
    """Service for pricing analysis and experimentation."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the PricingLabService.

        Args:
            db_session: Optional database session. If not provided, a new one will be created.
        """
        self.db = db_session if db_session else ScopedSession()

    def get_price_history(
        self, product_id: int, days: int = 30, source: Optional[str] = None
    ) -> List[Dict]:
        """Get price history for a product.

        Args:
            product_id: ID of the product
            days: Number of days of history to return
            source: Optional source filter (e.g., 'amazon', 'walmart')

        Returns:
            List of price snapshots with timestamps
        """
        query = self.db.query(PricingSnapshot).filter(
            PricingSnapshot.product_id == product_id,
            PricingSnapshot.captured_at >= datetime.utcnow() - timedelta(days=days),
        )

        if source:
            query = query.filter(PricingSnapshot.source == source)

        snapshots = query.order_by(PricingSnapshot.captured_at).all()

        return [
            {
                "timestamp": s.captured_at.isoformat(),
                "price": float(s.sale_price) if s.sale_price else float(s.base_price),
                "source": s.source,
                "in_stock": bool(s.in_stock),
                "is_on_sale": bool(s.is_on_sale),
                "stock_quantity": s.stock_quantity,
                "metadata": s.metadata_ or {},
            }
            for s in snapshots
        ]

    def get_competitor_pricing(self, product_id: int, days: int = 7) -> Dict[str, List[Dict]]:
        """Get competitor pricing data for a product.

        Args:
            product_id: ID of the product
            days: Number of days of history to return

        Returns:
            Dictionary mapping competitor names to their price histories
        """
        # Get the product to find similar products
        product = self.db.query(Product).get(product_id)
        if not product:
            return {}

        # In a real implementation, you would have a way to find similar/competing products
        # For now, we'll just get all pricing data for this product from different sources

        # Get all pricing snapshots for this product from different sources
        snapshots = (
            self.db.query(PricingSnapshot)
            .filter(
                PricingSnapshot.product_id == product_id,
                PricingSnapshot.captured_at >= datetime.utcnow() - timedelta(days=days),
                PricingSnapshot.source != "api",  # Exclude our own prices
            )
            .order_by(PricingSnapshot.source, PricingSnapshot.captured_at)
            .all()
        )

        # Group by source
        competitor_data = {}
        for snapshot in snapshots:
            if snapshot.source not in competitor_data:
                competitor_data[snapshot.source] = []

            competitor_data[snapshot.source].append(
                {
                    "timestamp": snapshot.captured_at.isoformat(),
                    "price": (
                        float(snapshot.sale_price)
                        if snapshot.sale_price
                        else float(snapshot.base_price)
                    ),
                    "in_stock": bool(snapshot.in_stock),
                    "is_on_sale": bool(snapshot.is_on_sale),
                    "stock_quantity": snapshot.stock_quantity,
                    "shipping_cost": (
                        float(snapshot.shipping_cost)
                        if snapshot.shipping_cost is not None
                        else None
                    ),
                    "free_shipping": bool(snapshot.free_shipping),
                    "metadata": snapshot.metadata_ or {},
                }
            )

        return competitor_data

    def analyze_price_elasticity(self, product_id: int, days: int = 90) -> Dict[str, float]:
        """Analyze price elasticity for a product.

        This calculates how sensitive demand is to price changes.

        Args:
            product_id: ID of the product
            days: Number of days of history to analyze

        Returns:
            Dictionary with elasticity metrics
        """
        # Get sales and pricing data (in a real app, this would come from your order history)
        # For now, we'll use a simplified approach with mock data

        # Mock data: price and quantity sold at different price points
        # In a real implementation, this would come from your order history
        price_points = [
            (19.99, 150),  # (price, quantity)
            (21.99, 140),
            (24.99, 120),
            (27.99, 90),
            (29.99, 80),
        ]

        # Calculate price elasticity using the midpoint formula
        # Elasticity = (% change in quantity) / (% change in price)
        elasticities = []
        for i in range(1, len(price_points)):
            price1, qty1 = price_points[i - 1]
            price2, qty2 = price_points[i]

            price_pct_change = (price2 - price1) / ((price1 + price2) / 2)
            qty_pct_change = (qty2 - qty1) / ((qty1 + qty2) / 2)

            if price_pct_change != 0:
                elasticity = qty_pct_change / price_pct_change
                elasticities.append(elasticity)

        avg_elasticity = sum(elasticities) / len(elasticities) if elasticities else 0

        return {
            "price_elasticity": avg_elasticity,
            "elasticity_interpretation": self._get_elasticity_interpretation(avg_elasticity),
            "recommended_price": self._calculate_optimal_price(price_points, avg_elasticity),
            "price_points_analyzed": len(price_points),
            "analysis_period_days": days,
        }

    def _get_elasticity_interpretation(self, elasticity: float) -> str:
        """Get a human-readable interpretation of the elasticity value."""
        if elasticity < -1:
            return "Highly elastic (demand is very sensitive to price changes)"
        elif -1 <= elasticity < -0.5:
            return "Elastic (demand is somewhat sensitive to price changes)"
        elif -0.5 <= elasticity <= 0.5:
            return "Unit elastic (demand changes proportionally with price)"
        elif 0.5 < elasticity <= 1:
            return "Inelastic (demand is not very sensitive to price changes)"
        else:
            return "Highly inelastic (demand is not sensitive to price changes)"

    def _calculate_optimal_price(
        self, price_points: List[Tuple[float, int]], elasticity: float
    ) -> float:
        """Calculate the optimal price based on elasticity and cost.

        This is a simplified version that just finds the price point with the highest revenue.
        In a real implementation, you would consider costs, margins, and other factors.
        """
        if not price_points:
            return 0.0

        # Find the price point with the highest revenue (price * quantity)
        max_revenue = 0
        optimal_price = price_points[0][0]

        for price, quantity in price_points:
            revenue = price * quantity
            if revenue > max_revenue:
                max_revenue = revenue
                optimal_price = price

        return optimal_price

    def create_pricing_experiment(
        self,
        name: str,
        product_ids: List[int],
        base_price: float,
        test_price: float,
        start_date: datetime,
        end_date: datetime,
        sample_size: int = 1000,
        traffic_allocation: int = 50,
        metadata: Optional[Dict] = None,
    ) -> PricingExperiment:
        """Create a new pricing experiment.

        Args:
            name: Name of the experiment
            product_ids: List of product IDs to include in the experiment
            base_price: The control price (current price)
            test_price: The price to test
            start_date: When the experiment should start
            end_date: When the experiment should end
            sample_size: Number of users to include in the experiment
            traffic_allocation: Percentage of traffic to allocate to the test group (0-100)
            metadata: Additional metadata for the experiment

        Returns:
            The created PricingExperiment object
        """
        if traffic_allocation < 0 or traffic_allocation > 100:
            raise ValueError("Traffic allocation must be between 0 and 100")

        if start_date >= end_date:
            raise ValueError("End date must be after start date")

        # Create the experiment
        experiment = PricingExperiment(
            name=name,
            description=f"A/B test for {len(product_ids)} products",
            start_date=start_date,
            end_date=end_date,
            is_active=0,  # Will be activated by the scheduler
            base_price=base_price,
            test_price=test_price,
            sample_size=sample_size,
            traffic_allocation=traffic_allocation,
            metadata_=metadata or {},
        )

        self.db.add(experiment)
        self.db.commit()

        return experiment

    def get_experiment_results(self, experiment_id: int) -> Dict:
        """Get results for a pricing experiment.

        Args:
            experiment_id: ID of the experiment

        Returns:
            Dictionary with experiment results
        """
        experiment = self.db.query(PricingExperiment).get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        # In a real implementation, you would query your analytics database
        # to get the actual results of the experiment

        # Mock data for demonstration
        return {
            "experiment_id": experiment.id,
            "name": experiment.name,
            "status": "completed" if experiment.end_date < datetime.utcnow() else "running",
            "start_date": experiment.start_date.isoformat(),
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
            "base_price": float(experiment.base_price),
            "test_price": float(experiment.test_price),
            "sample_size": experiment.sample_size,
            "traffic_allocation": experiment.traffic_allocation,
            "control_group_size": 500,  # Mock data
            "test_group_size": 500,  # Mock data
            "control_group_conversion": 0.05,  # 5% conversion
            "test_group_conversion": 0.065,  # 6.5% conversion
            "conversion_lift": 0.015,  # 1.5% lift
            "confidence_level": 95.0,  # 95% confidence
            "p_value": 0.03,  # Statistically significant
            "recommendation": "Implement test price" if 0.03 < 0.05 else "Keep current price",
            "estimated_annual_impact": {
                "revenue_impact": 12500.00,  # $12.5K
                "order_impact": 250,  # 250 more orders
                "customer_impact": 0.015,  # 1.5% more customers
            },
            "metadata": experiment.metadata_ or {},
        }

    def get_pricing_recommendations(
        self,
        product_id: int,
        competitor_weight: float = 0.4,
        elasticity_weight: float = 0.3,
        margin_weight: float = 0.3,
    ) -> Dict:
        """Get pricing recommendations for a product.

        Args:
            product_id: ID of the product
            competitor_weight: Weight for competitor pricing in the recommendation (0-1)
            elasticity_weight: Weight for price elasticity (0-1)
            margin_weight: Weight for profit margin (0-1)

        Returns:
            Dictionary with pricing recommendations
        """
        # Validate weights
        total_weight = competitor_weight + elasticity_weight + margin_weight
        if abs(total_weight - 1.0) > 0.01:  # Allow for floating point imprecision
            # Normalize weights
            total = competitor_weight + elasticity_weight + margin_weight
            competitor_weight /= total
            elasticity_weight /= total
            margin_weight = 1.0 - competitor_weight - elasticity_weight

        # Get product data
        product = self.db.query(Product).get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        # Get competitor pricing (simplified)
        competitor_prices = [19.99, 20.49, 21.99, 19.50, 22.50]  # Mock data
        avg_competitor_price = (
            sum(competitor_prices) / len(competitor_prices) if competitor_prices else 0
        )

        # Get price elasticity (simplified)
        elasticity_data = self.analyze_price_elasticity(product_id)
        elasticity = elasticity_data.get("price_elasticity", 0)

        # Get cost and current price (mock data)
        cost = 12.00  # In a real app, this would come from your product data
        current_price = float(product.price) if product.price else 0

        # Calculate recommended price using weighted factors
        competitor_factor = avg_competitor_price * competitor_weight

        # For elasticity, if demand is elastic (elasticity < -1), we might want to lower the price
        # If inelastic (elasticity > -1), we might be able to raise the price
        elasticity_adjustment = 1.0
        if elasticity < -1.5:  # Highly elastic
            elasticity_adjustment = 0.9  # 10% decrease
        elif elasticity < -1.0:  # Elastic
            elasticity_adjustment = 0.95  # 5% decrease
        elif elasticity > 0.5:  # Inelastic
            elasticity_adjustment = 1.05  # 5% increase

        elasticity_factor = current_price * elasticity_adjustment * elasticity_weight

        # For margin, aim for a target margin (e.g., 30%)
        target_margin = 0.30
        margin_price = cost / (1 - target_margin)
        margin_factor = margin_price * margin_weight

        # Calculate recommended price
        recommended_price = competitor_factor + elasticity_factor + margin_factor

        # Apply constraints (e.g., min/max price, psychological pricing)
        min_price = cost * 1.1  # At least 10% above cost
        max_price = avg_competitor_price * 1.2  # No more than 20% above average competitor

        recommended_price = max(min_price, min(recommended_price, max_price))

        # Apply psychological pricing (e.g., $19.99 instead of $20.00)
        recommended_price = self._apply_psychological_pricing(recommended_price)

        return {
            "product_id": product_id,
            "product_name": product.name,
            "current_price": current_price,
            "recommended_price": round(recommended_price, 2),
            "price_change_pct": (
                round(((recommended_price - current_price) / current_price * 100), 1)
                if current_price > 0
                else 0
            ),
            "factors": {
                "competitor_pricing": {
                    "weight": competitor_weight,
                    "avg_competitor_price": round(avg_competitor_price, 2),
                    "competitor_prices": competitor_prices,
                },
                "price_elasticity": {
                    "weight": elasticity_weight,
                    "elasticity": round(elasticity, 2),
                    "interpretation": elasticity_data.get("elasticity_interpretation", "Unknown"),
                },
                "profit_margin": {
                    "weight": margin_weight,
                    "cost": cost,
                    "target_margin": target_margin,
                    "min_price": round(min_price, 2),
                },
            },
            "constraints": {
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "applied_psychological_pricing": True,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _apply_psychological_pricing(self, price: float) -> float:
        """Apply psychological pricing (e.g., $19.99 instead of $20.00)."""
        # For prices >= $10, end with .99, .95, or .90
        if price >= 10:
            return int(price) + 0.99 if (price % 1) >= 0.5 else int(price) - 0.01
        # For prices < $10, use .95, .97, or .99
        elif price >= 1:
            return int(price) + 0.97 if (price % 1) >= 0.5 else int(price) - 0.03
        # For prices < $1, use .95, .97, or .99 cents
        else:
            return int(price * 100) / 100 + 0.99 / 100

    def get_pricing_dashboard_data(
        self, product_ids: Optional[List[int]] = None, days: int = 30
    ) -> Dict:
        """Get data for the pricing dashboard.

        Args:
            product_ids: Optional list of product IDs to include
            days: Number of days of history to include

        Returns:
            Dictionary with data for the pricing dashboard
        """
        # Get product pricing history
        query = self.db.query(
            Product.id,
            Product.name,
            Product.sku,
            func.avg(PricingSnapshot.base_price).label("avg_price"),
            func.avg(PricingSnapshot.sale_price).label("avg_sale_price"),
            func.count(PricingSnapshot.id).label("snapshot_count"),
        ).join(PricingSnapshot, Product.id == PricingSnapshot.product_id, isouter=True)

        if product_ids:
            query = query.filter(Product.id.in_(product_ids))

        query = query.filter(
            PricingSnapshot.captured_at >= datetime.utcnow() - timedelta(days=days)
        ).group_by(Product.id)

        products_data = []
        for row in query.all():
            products_data.append(
                {
                    "product_id": row.id,
                    "name": row.name,
                    "sku": row.sku,
                    "avg_price": float(row.avg_price) if row.avg_price else 0,
                    "avg_sale_price": float(row.avg_sale_price) if row.avg_sale_price else 0,
                    "snapshot_count": row.snapshot_count or 0,
                    "last_updated": datetime.utcnow().isoformat(),
                }
            )

        # Get active experiments
        active_experiments = (
            self.db.query(PricingExperiment)
            .filter(
                PricingExperiment.is_active == 1,
                or_(
                    PricingExperiment.end_date.is_(None),
                    PricingExperiment.end_date >= datetime.utcnow(),
                ),
            )
            .all()
        )

        return {
            "products": products_data,
            "active_experiments": [
                {
                    "id": exp.id,
                    "name": exp.name,
                    "start_date": exp.start_date.isoformat(),
                    "end_date": exp.end_date.isoformat() if exp.end_date else None,
                    "base_price": float(exp.base_price) if exp.base_price else 0,
                    "test_price": float(exp.test_price) if exp.test_price else 0,
                    "sample_size": exp.sample_size or 0,
                    "traffic_allocation": exp.traffic_allocation or 0,
                }
                for exp in active_experiments
            ],
            "metrics": {
                "total_products": len(products_data),
                "products_on_sale": sum(1 for p in products_data if p["avg_sale_price"] > 0),
                "avg_price": (
                    sum(p["avg_price"] for p in products_data if p["avg_price"])
                    / len([p for p in products_data if p["avg_price"]])
                    if products_data
                    else 0
                ),
                "active_experiments": len(active_experiments),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }


# Create a singleton instance for easy import
pricing_lab = PricingLabService()


def get_pricing_lab() -> PricingLabService:
    """Get a PricingLabService instance."""
    return pricing_lab
