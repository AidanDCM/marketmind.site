from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...executor import execute_all_approved, execute_approved, execution_log

router = APIRouter(tags=["execution"])


class ExecuteRequest(BaseModel):
    # dry_run defaults to True: the API never triggers a live action implicitly.
    dry_run: bool = True


@router.post("/{approval_id}")
def execute_one_endpoint(approval_id: str, body: ExecuteRequest, request: Request) -> dict:
    """Execute a single APPROVED action. dry_run defaults to True."""
    engine = request.app.state.engine
    try:
        result = execute_approved(engine, approval_id, dry_run=body.dry_run)
    except KeyError:
        detail = f"Approval {approval_id!r} not found."
        raise HTTPException(status_code=404, detail=detail) from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return result.to_dict()


@router.post("")
def execute_all_endpoint(body: ExecuteRequest, request: Request) -> list[dict]:
    """Execute every un-executed APPROVED action. Per-action refusals are captured."""
    engine = request.app.state.engine
    results = execute_all_approved(engine, dry_run=body.dry_run)
    return [r.to_dict() for r in results]


@router.get("/log")
def execution_log_endpoint(request: Request) -> list[dict]:
    """Return the append-only log of executed actions, oldest first."""
    engine = request.app.state.engine
    return execution_log(engine)
