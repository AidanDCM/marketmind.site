import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from packages.database.models.user import User as DBUser
from packages.orders.exceptions import ExceptionKind, ExceptionsService
from packages.orders.fulfillment import FulfillmentService, Tracking
from packages.orders.kpis import KPIService
from packages.orders.po_cj import CJPOClient
from packages.orders.routing import RoutingEngine
from packages.shared.config import get_settings
from packages.shared.db import get_db

router = APIRouter(prefix="/orders", tags=["orders"])

# Simple service singletons for now; replace with DI container as needed
exceptions_service = ExceptionsService()
kpi_service = KPIService()
routing_engine = RoutingEngine(guardrails={"max_cost_cents": 1500})
po_client = CJPOClient(api_key=os.getenv("CJ_API_KEY"))
fulfillment_service = FulfillmentService(
    easypost_key=os.getenv("EASYPOST_API_KEY"), shippo_key=os.getenv("SHIPPO_API_KEY")
)
settings = get_settings()
oauth2_optional = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)

# Optional Sentry breadcrumbs for key order operations
try:  # pragma: no cover - optional dependency
    import sentry_sdk  # type: ignore
except Exception:  # pragma: no cover
    sentry_sdk = None  # type: ignore

def _sentry_breadcrumb(level: str, category: str, message: str, data: Optional[dict] = None) -> None:
    if sentry_sdk is None:
        return
    try:  # pragma: no cover
        sentry_sdk.add_breadcrumb(
            type="default",
            category=category,
            message=message,
            level=level,
            data=data or {},
        )
    except Exception:
        pass


def audit_log(
    action: str, order_id: int, user: Optional[DBUser], extra: Optional[dict] = None
) -> None:
    who = user.username if user else "anonymous"
    payload = {"action": action, "order_id": order_id, "who": who}
    if extra:
        payload.update(extra)
    # Replace with structured logger or DB persistence as needed
    print(f"AUDIT {payload}")
    # Add Sentry breadcrumb for observability (no-op if Sentry unavailable)
    _sentry_breadcrumb(
        level="info",
        category="orders",
        message=f"order.{action}",
        data=payload,
    )


async def optional_auth(
    token: Optional[str] = Depends(oauth2_optional), db: Session = Depends(get_db)  # noqa: B008
) -> Optional[DBUser]:
    """Optional auth: if ORDERS_REQUIRE_AUTH=true, require a valid bearer token;
    otherwise allow anonymous calls. When token is present, validate and load user.
    """
    # Evaluate the auth requirement dynamically to allow runtime toggling in tests/env
    require_auth = os.getenv("ORDERS_REQUIRE_AUTH", "false").lower() == "true"
    if not require_auth:
        # Anonymous allowed for verification and local dev
        if not token:
            return None
    # If we reach here and no token, enforce auth
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(DBUser).filter(DBUser.username == username).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user
    except JWTError as e:
        raise HTTPException(status_code=401, detail="Invalid token") from e


class ExceptionRequest(BaseModel):
    kind: str
    note: Optional[str] = None


@router.get("/kpis")
def kpis(db: Session = Depends(get_db)):  # noqa: B008
    snap = kpi_service.compute(db)
    return {"lsr_pct": snap.lsr_pct, "vtr_pct": snap.vtr_pct, "odr_pct": snap.odr_pct}


@router.post("/{order_id}/reprocess")
def reprocess(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # TODO: enqueue background reprocess task
    audit_log("reprocess", order_id, user)
    return {"order_id": order_id, "queued": True, "action": "reprocess"}


@router.post("/{order_id}/route")
def force_route(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # Minimal route using routing engine
    decision = routing_engine.route(
        {
            "buyer_region": {"country": "US", "state": "CA", "postal_code": "94016"},
            "items": [{"sku": "TEST-SKU", "qty": 1}],
            "weight_oz": 16,
        }
    )
    audit_log("route", order_id, user, {"supplier_id": decision.supplier_id})
    return {
        "order_id": order_id,
        "routed": decision.supplier_id is not None,
        "supplier_id": decision.supplier_id,
        "carrier": decision.ship_carrier,
        "service": decision.ship_service,
        "explanation": decision.explanation,
    }


@router.post("/{order_id}/po")
def create_po(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # Minimal idempotent CJ PO creation (simulation)
    payload = {"order_id": order_id, "items": [("TEST-SKU", 1)]}
    res = po_client.create_po(payload)
    audit_log("create_po", order_id, user, {"supplier_po_ref": res.supplier_po_ref})
    return {
        "order_id": order_id,
        "po_created": True,
        "supplier_po_ref": res.supplier_po_ref,
        "idempotency_key": res.idempotency_key,
    }


@router.post("/{order_id}/fulfill")
def fulfill(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # Minimal shipment purchase + publish tracking (simulation)
    label = fulfillment_service.buy_label(
        {"to": {"zip": "94016"}, "from": {"zip": "10001"}, "weight_oz": 16}
    )
    tracking = Tracking(
        carrier=label.get("carrier", "UPS"),
        service=label.get("service", "Ground"),
        tracking_no="1ZSIMULATE",
    )
    ok = fulfillment_service.publish_tracking("amazon", str(order_id), tracking)
    audit_log("fulfill", order_id, user, {"tracking_no": tracking.tracking_no})
    return {"order_id": order_id, "fulfilled": ok, "tracking": tracking.__dict__, "label": label}


@router.post("/{order_id}/cancel")
def cancel(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # Stub: cancel flow
    audit_log("cancel", order_id, user)
    return {"order_id": order_id, "canceled": True}


@router.post("/{order_id}/refund")
def refund(order_id: int, user: Optional[DBUser] = Depends(optional_auth)):  # noqa: B008
    # Stub: refund flow
    audit_log("refund", order_id, user)
    return {"order_id": order_id, "refunded": True}


@router.post("/{order_id}/exception")
def open_exception(
    order_id: int, req: ExceptionRequest, user: Optional[DBUser] = Depends(optional_auth)  # noqa: B008
):
    try:
        ticket = exceptions_service.open(
            order_id=order_id,
            kind=ExceptionKind[req.kind.upper()],
            note=req.note,
        )
    except KeyError as err:
        raise HTTPException(status_code=400, detail="Invalid exception kind") from err
    except ValueError as err:
        raise HTTPException(status_code=400, detail="Invalid exception kind") from err
    audit_log("exception", order_id, user, {"kind": ticket.kind})
    return {
        "order_id": order_id,
        "exception": ticket.kind,
        "state": ticket.state,
        "note": ticket.note,
    }


@router.get("/{order_id}")
def get_order(
    order_id: int, db: Session = Depends(get_db), user: Optional[DBUser] = Depends(optional_auth)  # noqa: B008
):
    # Stub: replace with real query join once state machine is aligned
    audit_log("get_order", order_id, user)
    return {"order_id": order_id, "status": "stub", "message": "Order detail stub"}
