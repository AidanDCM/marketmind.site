"""Unit economics endpoint — exposes the math engine (Slice 1).

Pure computation: no external calls, no spending, no DB writes.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...math_engine import calculate_unit_economics
from ...schemas import ProductCostInput

router = APIRouter(tags=["economics"])


class EconomicsRequest(BaseModel):
    product_name: str
    sale_price: float
    product_cost: float
    packaging_cost: float = 0.0
    shipping_cost: float = 0.0
    platform_fee: float = 0.0
    payment_fee: float = 0.0
    refund_allowance: float = 0.0
    software_allocation: float = 0.0
    estimated_cac: float = 0.0


@router.post("")
def economics_endpoint(req: EconomicsRequest) -> dict:
    product = ProductCostInput(**req.model_dump())
    return calculate_unit_economics(product).to_dict()
