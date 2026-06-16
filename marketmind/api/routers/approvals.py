from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...db import approval_store
from ...schemas import ApprovalStatus

router = APIRouter(tags=["approvals"])


class ApproveRequest(BaseModel):
    note: str = ""


@router.get("")
def list_approvals_endpoint(request: Request, status: str | None = None) -> list[dict]:
    engine = request.app.state.engine
    filter_status = ApprovalStatus(status) if status else None
    records = approval_store.list_approvals(engine, status=filter_status)
    return [r.to_dict() for r in records]


@router.get("/pending")
def list_pending_endpoint(request: Request) -> list[dict]:
    engine = request.app.state.engine
    return [r.to_dict() for r in approval_store.list_pending(engine)]


@router.get("/{approval_id}")
def get_approval_endpoint(approval_id: str, request: Request) -> dict:
    engine = request.app.state.engine
    record = approval_store.get_approval(engine, approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Approval {approval_id!r} not found.")
    return record.to_dict()


@router.post("/{approval_id}/approve")
def approve_endpoint(approval_id: str, body: ApproveRequest, request: Request) -> dict:
    engine = request.app.state.engine
    try:
        record = approval_store.approve(engine, approval_id, note=body.note)
    except KeyError:
        detail = f"Approval {approval_id!r} not found."
        raise HTTPException(status_code=404, detail=detail) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record.to_dict()


@router.post("/{approval_id}/deny")
def deny_endpoint(approval_id: str, body: ApproveRequest, request: Request) -> dict:
    engine = request.app.state.engine
    try:
        record = approval_store.deny(engine, approval_id, note=body.note)
    except KeyError:
        detail = f"Approval {approval_id!r} not found."
        raise HTTPException(status_code=404, detail=detail) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return record.to_dict()
