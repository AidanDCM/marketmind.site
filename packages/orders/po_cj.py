"""CJ Dropshipping PO integration (scaffold).

Provides idempotent PO creation and tracking polling.
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class POResult:
    supplier_po_ref: str
    status: str
    idempotency_key: str
    simulated: bool = True


class CJPOClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        # Simple in-memory idempotency store: idem_key -> supplier_po_ref
        # In production, persist in DB
        if not hasattr(self.__class__, "_idem_store"):
            self.__class__._idem_store = {}

    def _make_idempotency_key(self, order_payload: Dict[str, Any]) -> str:
        raw = str(sorted(order_payload.items())).encode()
        return hashlib.sha256(raw).hexdigest()[:24]

    def create_po(self, order_payload: Dict[str, Any]) -> POResult:
        # TODO: call CJ API; respect idempotency key and retries
        idem = self._make_idempotency_key(order_payload)
        store: Dict[str, str] = self.__class__._idem_store  # type: ignore[attr-defined]
        if idem in store:
            ref = store[idem]
            return POResult(supplier_po_ref=ref, status="created", idempotency_key=idem)
        # Simulate network delay
        time.sleep(0.01)
        ref = f"PO-{idem[:8].upper()}"
        store[idem] = ref
        return POResult(supplier_po_ref=ref, status="created", idempotency_key=idem)

    def get_tracking(self, supplier_po_ref: str) -> Dict[str, Any]:
        # TODO: poll CJ for tracking; map carrier/service names
        return {"carrier": "UPS", "service": "Ground", "tracking_no": f"1Z{supplier_po_ref[-8:]}"}
