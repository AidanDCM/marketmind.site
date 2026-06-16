from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ...pipeline import prepare_offer_for_approval
from ...schemas import OfferContext

router = APIRouter(tags=["pipeline"])


class PrepareOfferRequest(BaseModel):
    product_name: str
    sale_price: float
    key_benefit: str
    target_customer: str
    secondary_benefits: list[str] = []
    common_objections: list[str] = []
    shipping_note: str = ""
    return_policy: str = ""
    niche: str = ""
    channel: str = "stripe"
    vendor: str = "MarketMind"
    product_type: str = ""


@router.post("/prepare-offer")
def prepare_offer_endpoint(req: PrepareOfferRequest, request: Request) -> dict:
    """Build spec + payload, create a gated approval, attach the payload.

    Returns the resulting (PENDING) approval record.
    """
    ctx = OfferContext(
        product_name=req.product_name,
        sale_price=req.sale_price,
        key_benefit=req.key_benefit,
        target_customer=req.target_customer,
        secondary_benefits=tuple(req.secondary_benefits),
        common_objections=tuple(req.common_objections),
        shipping_note=req.shipping_note,
        return_policy=req.return_policy,
        niche=req.niche,
    )
    engine = request.app.state.engine
    record = prepare_offer_for_approval(
        engine, ctx, channel=req.channel, vendor=req.vendor, product_type=req.product_type
    )
    return record.to_dict()
