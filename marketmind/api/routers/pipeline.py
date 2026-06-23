from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...executor import get_action_payload
from ...pipeline import prepare_offer_for_approval, prepare_supplier_outreach_for_approval
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


class PrepareSupplierOutreachRequest(BaseModel):
    supplier_name: str
    product_name: str
    sample_quantity: int = 1
    target_unit_cost: float | None = None
    operator_note: str = ""
    expected_cost: float = 0.0


@router.post("/prepare-supplier-outreach")
def prepare_supplier_outreach_endpoint(
    req: PrepareSupplierOutreachRequest,
    request: Request,
) -> dict:
    """Build a supplier email draft and create a gated contact_supplier approval."""
    engine = request.app.state.engine
    try:
        record = prepare_supplier_outreach_for_approval(
            engine,
            supplier_name=req.supplier_name,
            product_name=req.product_name,
            sample_quantity=req.sample_quantity,
            target_unit_cost=req.target_unit_cost,
            operator_note=req.operator_note,
            expected_cost=req.expected_cost,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return record.to_dict()


@router.get("/outreach-draft/{approval_id}")
def get_outreach_draft_endpoint(approval_id: str, request: Request) -> dict:
    """Return the supplier outreach draft payload attached to an approval."""
    engine = request.app.state.engine
    payload = get_action_payload(engine, approval_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="No outreach draft found for this approval")
    return payload
