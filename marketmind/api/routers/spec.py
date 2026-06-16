from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...schemas import OfferContext
from ...spec_generator import generate_offer_spec

router = APIRouter(tags=["spec"])


class SpecRequest(BaseModel):
    product_name: str
    sale_price: float
    key_benefit: str
    target_customer: str
    secondary_benefits: list[str] = []
    common_objections: list[str] = []
    shipping_note: str = ""
    return_policy: str = ""
    niche: str = ""


@router.post("")
def generate_spec_endpoint(req: SpecRequest) -> dict:
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
    return generate_offer_spec(ctx).to_dict()
