from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from apps.hive_api.security import SubjectScope, get_subject_scope_optional
from packages.database.models import (
    AttributionEvent,
    BundleTrial,
    Campaign,
    CampaignAsset,
    CustomerJourney,
    Experiment,
    ExperimentResult,
    ExperimentVariant,
)
from packages.shared.db import get_db

router = APIRouter()


class CampaignIn(BaseModel):
    name: str = Field(..., max_length=255)
    org_id: Optional[str] = Field(None, description="Organization scope")
    brain_id: Optional[str] = Field(None, description="Brain scope")
    status: Optional[str] = Field("draft", description="draft|active|paused|archived")
    meta: Optional[str] = None


class CampaignOut(BaseModel):
    id: int
    name: str
    org_id: Optional[str]
    brain_id: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/campaigns", response_model=List[CampaignOut])
def list_campaigns(
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    """List campaigns (scoped)."""
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])

    q = db.query(Campaign)
    if org_id:
        q = q.filter(Campaign.org_id == org_id)
    if brain_id:
        q = q.filter(Campaign.brain_id == brain_id)
    return q.order_by(Campaign.id.desc()).limit(200).all()


@router.post("/campaigns", response_model=CampaignOut)
def create_campaign(
    payload: CampaignIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    """Create a campaign. Enforces subject scope and defaults status to draft."""
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )

    obj = Campaign(
        name=payload.name,
        org_id=payload.org_id,
        brain_id=payload.brain_id,
        status=payload.status or "draft",
        meta=payload.meta,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Experiment Variants ---


class VariantIn(BaseModel):
    experiment_id: int
    key: str = Field(..., max_length=64)
    name: Optional[str] = Field(None, max_length=255)
    params: Optional[str] = None
    allocation_weight: Optional[float] = 1.0
    status: Optional[str] = Field("active", max_length=32)


class VariantOut(BaseModel):
    id: int
    experiment_id: int
    key: str
    name: Optional[str]
    allocation_weight: float
    status: str

    class Config:
        from_attributes = True


@router.get("/variants", response_model=List[VariantOut])
def list_variants(
    experiment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    # Scope via parent experiment as needed
    q = db.query(ExperimentVariant)
    if experiment_id:
        q = q.filter(ExperimentVariant.experiment_id == experiment_id)
    return q.order_by(ExperimentVariant.id.desc()).limit(200).all()


@router.post("/variants", response_model=VariantOut)
def create_variant(
    payload: VariantIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    exp = db.query(Experiment).filter(Experiment.id == payload.experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="experiment not found")
    # Enforce subject scope using experiment's org/brain if provided
    sub.ensure_scope(req_org_id=exp.org_id, req_brain_ids=[exp.brain_id] if exp.brain_id else [])
    obj = ExperimentVariant(
        experiment_id=payload.experiment_id,
        key=payload.key,
        name=payload.name,
        params=payload.params,
        allocation_weight=payload.allocation_weight or 1.0,
        status=payload.status or "active",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Bundle Trials ---


class BundleTrialIn(BaseModel):
    experiment_id: Optional[int] = None
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    bundle_ref: str = Field(..., max_length=128)
    components: Optional[str] = None
    channel: Optional[str] = Field(None, max_length=64)
    status: Optional[str] = Field("draft", max_length=32)
    guardrail_flags: Optional[str] = None


class BundleTrialOut(BaseModel):
    id: int
    experiment_id: Optional[int]
    bundle_ref: str
    channel: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/bundles", response_model=List[BundleTrialOut])
def list_bundles(
    experiment_id: Optional[int] = None,
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(BundleTrial)
    if experiment_id:
        q = q.filter(BundleTrial.experiment_id == experiment_id)
    if org_id:
        q = q.filter(BundleTrial.org_id == org_id)
    if brain_id:
        q = q.filter(BundleTrial.brain_id == brain_id)
    if status:
        q = q.filter(BundleTrial.status == status)
    return q.order_by(BundleTrial.id.desc()).limit(200).all()


@router.post("/bundles", response_model=BundleTrialOut)
def create_bundle(
    payload: BundleTrialIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    # If experiment provided, scope by it, and default org/brain from it
    org_id = payload.org_id
    brain_id = payload.brain_id
    if payload.experiment_id:
        exp = db.query(Experiment).filter(Experiment.id == payload.experiment_id).first()
        if not exp:
            raise HTTPException(status_code=404, detail="experiment not found")
        org_id = org_id or exp.org_id
        brain_id = brain_id or exp.brain_id
        sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    else:
        sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])

    obj = BundleTrial(
        experiment_id=payload.experiment_id,
        org_id=org_id,
        brain_id=brain_id,
        bundle_ref=payload.bundle_ref,
        components=payload.components,
        channel=payload.channel,
        status=payload.status or "draft",
        guardrail_flags=payload.guardrail_flags,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Experiment Results ---


class ExperimentResultIn(BaseModel):
    experiment_id: int
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    variant: str = Field(..., max_length=32)
    metric: str = Field(..., max_length=64)
    value: float = 0.0
    sample_size: Optional[int] = None
    notes: Optional[str] = None
    observed_at: Optional[str] = None


class ExperimentResultOut(BaseModel):
    id: int
    experiment_id: int
    variant: str
    metric: str
    value: float

    class Config:
        from_attributes = True


@router.get("/experiment-results", response_model=List[ExperimentResultOut])
def list_experiment_results(
    experiment_id: Optional[int] = None,
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    metric: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(ExperimentResult)
    if experiment_id:
        q = q.filter(ExperimentResult.experiment_id == experiment_id)
    if org_id:
        q = q.filter(ExperimentResult.org_id == org_id)
    if brain_id:
        q = q.filter(ExperimentResult.brain_id == brain_id)
    if metric:
        q = q.filter(ExperimentResult.metric == metric)
    return q.order_by(ExperimentResult.id.desc()).limit(200).all()


@router.post("/experiment-results", response_model=ExperimentResultOut)
def create_experiment_result(
    payload: ExperimentResultIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )
    exp = db.query(Experiment).filter(Experiment.id == payload.experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="experiment not found")
    obj = ExperimentResult(
        experiment_id=payload.experiment_id,
        org_id=payload.org_id or exp.org_id,
        brain_id=payload.brain_id or exp.brain_id,
        variant=payload.variant,
        metric=payload.metric,
        value=payload.value,
        sample_size=payload.sample_size,
        notes=payload.notes,
        observed_at=payload.observed_at,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Attribution Events ---


class AttributionIn(BaseModel):
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    campaign_id: Optional[int] = None
    source: Optional[str] = Field(None, max_length=64)
    medium: Optional[str] = Field(None, max_length=64)
    channel: Optional[str] = Field(None, max_length=64)
    event: str = Field(..., max_length=64)
    value: Optional[float] = None
    currency: Optional[str] = Field(None, max_length=8)
    customer_ref: Optional[str] = Field(None, max_length=128)
    meta: Optional[str] = None


class AttributionOut(BaseModel):
    id: int
    event: str
    campaign_id: Optional[int]
    source: Optional[str]
    medium: Optional[str]
    channel: Optional[str]

    class Config:
        from_attributes = True


@router.get("/attribution", response_model=List[AttributionOut])
def list_attribution(
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    campaign_id: Optional[int] = None,
    source: Optional[str] = None,
    event: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(AttributionEvent)
    if org_id:
        q = q.filter(AttributionEvent.org_id == org_id)
    if brain_id:
        q = q.filter(AttributionEvent.brain_id == brain_id)
    if campaign_id:
        q = q.filter(AttributionEvent.campaign_id == campaign_id)
    if source:
        q = q.filter(AttributionEvent.source == source)
    if event:
        q = q.filter(AttributionEvent.event == event)
    return q.order_by(AttributionEvent.id.desc()).limit(200).all()


@router.post("/attribution", response_model=AttributionOut)
def create_attribution(
    payload: AttributionIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )
    if payload.campaign_id:
        camp = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
        if not camp:
            raise HTTPException(status_code=404, detail="campaign not found")
        if not payload.org_id:
            payload.org_id = camp.org_id
        if not payload.brain_id:
            payload.brain_id = camp.brain_id
    obj = AttributionEvent(
        org_id=payload.org_id,
        brain_id=payload.brain_id,
        campaign_id=payload.campaign_id,
        source=payload.source,
        medium=payload.medium,
        channel=payload.channel,
        event=payload.event,
        value=payload.value,
        currency=payload.currency,
        customer_ref=payload.customer_ref,
        meta=payload.meta,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Customer Journey ---


class JourneyIn(BaseModel):
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    customer_ref: Optional[str] = Field(None, max_length=128)
    stage: str = Field(..., max_length=32)
    source: Optional[str] = Field(None, max_length=64)
    medium: Optional[str] = Field(None, max_length=64)
    campaign_id: Optional[int] = None
    meta: Optional[str] = None


class JourneyOut(BaseModel):
    id: int
    customer_ref: Optional[str]
    stage: str
    campaign_id: Optional[int]

    class Config:
        from_attributes = True


@router.get("/journeys", response_model=List[JourneyOut])
def list_journeys(
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    customer_ref: Optional[str] = None,
    stage: Optional[str] = None,
    campaign_id: Optional[int] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(CustomerJourney)
    if org_id:
        q = q.filter(CustomerJourney.org_id == org_id)
    if brain_id:
        q = q.filter(CustomerJourney.brain_id == brain_id)
    if customer_ref:
        q = q.filter(CustomerJourney.customer_ref == customer_ref)
    if stage:
        q = q.filter(CustomerJourney.stage == stage)
    if campaign_id:
        q = q.filter(CustomerJourney.campaign_id == campaign_id)
    return q.order_by(CustomerJourney.id.desc()).limit(200).all()


@router.post("/journeys", response_model=JourneyOut)
def create_journey(
    payload: JourneyIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )
    if payload.campaign_id:
        camp = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
        if not camp:
            raise HTTPException(status_code=404, detail="campaign not found")
        if not payload.org_id:
            payload.org_id = camp.org_id
        if not payload.brain_id:
            payload.brain_id = camp.brain_id
    obj = CustomerJourney(
        org_id=payload.org_id,
        brain_id=payload.brain_id,
        customer_ref=payload.customer_ref,
        stage=payload.stage,
        source=payload.source,
        medium=payload.medium,
        campaign_id=payload.campaign_id,
        meta=payload.meta,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Campaign Assets ---


class CampaignAssetIn(BaseModel):
    campaign_id: int
    kind: str = Field(..., max_length=32)
    name: Optional[str] = Field(None, max_length=255)
    data: Optional[str] = None
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    status: Optional[str] = Field("draft", max_length=32)


class CampaignAssetOut(BaseModel):
    id: int
    campaign_id: int
    kind: str
    name: Optional[str]
    status: str

    class Config:
        from_attributes = True


@router.get("/assets", response_model=List[CampaignAssetOut])
def list_assets(
    campaign_id: Optional[int] = None,
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(CampaignAsset)
    if campaign_id:
        q = q.filter(CampaignAsset.campaign_id == campaign_id)
    if org_id:
        q = q.filter(CampaignAsset.org_id == org_id)
    if brain_id:
        q = q.filter(CampaignAsset.brain_id == brain_id)
    return q.order_by(CampaignAsset.id.desc()).limit(200).all()


@router.post("/assets", response_model=CampaignAssetOut)
def create_asset(
    payload: CampaignAssetIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )
    # Ensure campaign exists (and optionally scoped)
    camp = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="campaign not found")
    obj = CampaignAsset(
        campaign_id=payload.campaign_id,
        kind=payload.kind,
        name=payload.name,
        data=payload.data,
        org_id=payload.org_id or camp.org_id,
        brain_id=payload.brain_id or camp.brain_id,
        status=payload.status or "draft",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --- Experiments ---


class ExperimentIn(BaseModel):
    campaign_id: int
    name: str = Field(..., max_length=255)
    kind: Optional[str] = Field("ab", max_length=32)
    hypothesis: Optional[str] = None
    org_id: Optional[str] = None
    brain_id: Optional[str] = None
    status: Optional[str] = Field("draft", max_length=32)


class ExperimentOut(BaseModel):
    id: int
    campaign_id: int
    name: str
    kind: str
    status: str

    class Config:
        from_attributes = True


@router.get("/experiments", response_model=List[ExperimentOut])
def list_experiments(
    campaign_id: Optional[int] = None,
    org_id: Optional[str] = None,
    brain_id: Optional[str] = None,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(req_org_id=org_id, req_brain_ids=[brain_id] if brain_id else [])
    q = db.query(Experiment)
    if campaign_id:
        q = q.filter(Experiment.campaign_id == campaign_id)
    if org_id:
        q = q.filter(Experiment.org_id == org_id)
    if brain_id:
        q = q.filter(Experiment.brain_id == brain_id)
    return q.order_by(Experiment.id.desc()).limit(200).all()


@router.post("/experiments", response_model=ExperimentOut)
def create_experiment(
    payload: ExperimentIn,
    db: Session = Depends(get_db),
    sub: SubjectScope = Depends(get_subject_scope_optional),
):
    sub.ensure_scope(
        req_org_id=payload.org_id, req_brain_ids=[payload.brain_id] if payload.brain_id else []
    )
    camp = db.query(Campaign).filter(Campaign.id == payload.campaign_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="campaign not found")
    obj = Experiment(
        campaign_id=payload.campaign_id,
        name=payload.name,
        kind=payload.kind or "ab",
        hypothesis=payload.hypothesis,
        org_id=payload.org_id or camp.org_id,
        brain_id=payload.brain_id or camp.brain_id,
        status=payload.status or "draft",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
