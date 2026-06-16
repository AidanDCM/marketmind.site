from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from ...schemas import NicheCandidate, ProductCandidate
from ...scoring import score_niche, score_product

router = APIRouter(tags=["scoring"])


class ProductScoreRequest(BaseModel):
    product_name: str
    est_sale_price: float
    est_product_cost: float
    est_shipping_cost: float = 0.0
    competition: float = 0.5
    return_risk: float = 0.3
    compliance_risk: float = 0.0
    content_potential: float = 0.5
    repeat_purchase_potential: float = 0.3
    personal_fit: float = 0.5
    supplier_reliability: float = 0.5
    evidence_quality: float = 0.3
    niche: str = ""


class NicheScoreRequest(BaseModel):
    niche_name: str
    demand: float = 0.5
    competition: float = 0.5
    margin_potential: float = 0.5
    content_potential: float = 0.5
    personal_fit: float = 0.5
    supplier_availability: float = 0.5
    repeat_purchase_potential: float = 0.3
    regulatory_risk: float = 0.0
    evidence_quality: float = 0.3


@router.post("/product")
def score_product_endpoint(req: ProductScoreRequest) -> dict:
    candidate = ProductCandidate(**req.model_dump())
    return score_product(candidate).to_dict()


@router.post("/niche")
def score_niche_endpoint(req: NicheScoreRequest) -> dict:
    candidate = NicheCandidate(**req.model_dump())
    return score_niche(candidate).to_dict()
