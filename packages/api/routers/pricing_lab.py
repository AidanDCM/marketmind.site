"""Pricing Lab API endpoints.

This module provides REST API endpoints for the Pricing Lab functionality.
"""

from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from packages.database import get_db
from packages.services.pricing_lab import PricingLabService

router = APIRouter(
    prefix="/pricing-lab",
    tags=["pricing-lab"],
    responses={404: {"description": "Not found"}},
)


# Request/Response Models
class PriceHistoryResponse(BaseModel):
    """Response model for price history endpoint."""

    product_id: int
    product_name: str
    history: List[dict]


class CompetitorPricingResponse(BaseModel):
    """Response model for competitor pricing endpoint."""

    product_id: int
    product_name: str
    competitors: dict


class PriceElasticityResponse(BaseModel):
    """Response model for price elasticity endpoint."""

    product_id: int
    price_elasticity: float
    elasticity_interpretation: str
    recommended_price: float
    price_points_analyzed: int
    analysis_period_days: int


class PricingExperimentCreate(BaseModel):
    """Request model for creating a pricing experiment."""

    name: str = Field(..., min_length=3, max_length=100)
    product_ids: List[int] = Field(..., min_items=1)
    base_price: float = Field(..., gt=0)
    test_price: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    sample_size: int = Field(1000, gt=0)
    traffic_allocation: int = Field(50, ge=1, le=100)
    metadata: Optional[dict] = None


class PricingRecommendationResponse(BaseModel):
    """Response model for pricing recommendations."""

    product_id: int
    product_name: str
    current_price: float
    recommended_price: float
    price_change_pct: float
    factors: dict
    constraints: dict
    timestamp: str


class PricingDashboardResponse(BaseModel):
    """Response model for pricing dashboard data."""

    products: List[dict]
    active_experiments: List[dict]
    metrics: dict
    timestamp: str


# API Endpoints
@router.get("/price-history/{product_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: int,
    days: Annotated[int, Query(30, ge=1, le=365, description="Number of days of history to return")],
    source: Annotated[Optional[str], Query(None, description="Filter by data source")],
    db: Annotated[Session, Depends(get_db)],
):
    """Get price history for a product."""
    service = PricingLabService(db)

    # Get the product name
    from packages.database.models import Product

    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    history = service.get_price_history(product_id, days=days, source=source)

    return {"product_id": product_id, "product_name": product.name, "history": history}


@router.get("/competitor-pricing/{product_id}", response_model=CompetitorPricingResponse)
async def get_competitor_pricing(
    product_id: int,
    days: Annotated[int, Query(7, ge=1, le=90, description="Number of days of history to return")],
    db: Annotated[Session, Depends(get_db)],
):
    """Get competitor pricing data for a product."""
    service = PricingLabService(db)

    # Get the product name
    from packages.database.models import Product

    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    competitors = service.get_competitor_pricing(product_id, days=days)

    return {"product_id": product_id, "product_name": product.name, "competitors": competitors}


@router.get("/price-elasticity/{product_id}", response_model=PriceElasticityResponse)
async def get_price_elasticity(
    product_id: int,
    days: Annotated[int, Query(90, ge=30, le=365, description="Number of days of history to analyze")],
    db: Annotated[Session, Depends(get_db)],
):
    """Analyze price elasticity for a product."""
    service = PricingLabService(db)

    # Verify the product exists
    from packages.database.models import Product

    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = service.analyze_price_elasticity(product_id, days=days)
    result["product_id"] = product_id

    return result


@router.post("/experiments", status_code=201)
async def create_experiment(
    experiment_data: PricingExperimentCreate, db: Annotated[Session, Depends(get_db)]
):
    """Create a new pricing experiment."""
    service = PricingLabService(db)

    try:
        experiment = service.create_pricing_experiment(
            name=experiment_data.name,
            product_ids=experiment_data.product_ids,
            base_price=experiment_data.base_price,
            test_price=experiment_data.test_price,
            start_date=experiment_data.start_date,
            end_date=experiment_data.end_date,
            sample_size=experiment_data.sample_size,
            traffic_allocation=experiment_data.traffic_allocation,
            metadata=experiment_data.metadata,
        )

        return {
            "id": experiment.id,
            "name": experiment.name,
            "status": "created",
            "start_date": experiment.start_date.isoformat(),
            "end_date": experiment.end_date.isoformat() if experiment.end_date else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: int, db: Annotated[Session, Depends(get_db)]
):
    """Get results for a pricing experiment."""
    service = PricingLabService(db)

    try:
        return service.get_experiment_results(experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/recommendations/{product_id}", response_model=PricingRecommendationResponse)
async def get_pricing_recommendations(
    product_id: int,
    competitor_weight: Annotated[
        float, Query(0.4, ge=0, le=1, description="Weight for competitor pricing (0-1)")
    ],
    elasticity_weight: Annotated[
        float, Query(0.3, ge=0, le=1, description="Weight for price elasticity (0-1)")
    ],
    margin_weight: Annotated[
        float, Query(0.3, ge=0, le=1, description="Weight for profit margin (0-1)")
    ],
    db: Annotated[Session, Depends(get_db)],
):
    """Get pricing recommendations for a product."""
    service = PricingLabService(db)

    # Verify the product exists
    from packages.database.models import Product

    product = db.query(Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        return service.get_pricing_recommendations(
            product_id=product_id,
            competitor_weight=competitor_weight,
            elasticity_weight=elasticity_weight,
            margin_weight=margin_weight,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/dashboard", response_model=PricingDashboardResponse)
async def get_pricing_dashboard(
    product_ids: Annotated[Optional[List[int]], Query(None, description="Filter by product IDs")],
    days: Annotated[int, Query(30, ge=1, le=365, description="Number of days of history to include")],
    db: Annotated[Session, Depends(get_db)],
):
    """Get data for the pricing dashboard."""
    service = PricingLabService(db)
    return service.get_pricing_dashboard_data(product_ids=product_ids, days=days)
