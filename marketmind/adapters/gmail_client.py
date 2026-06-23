"""Gmail draft client — simulated by default; live API deferred.

When ``MARKETMIND_GMAIL_ENABLED`` is true and credentials are set, approved
``contact_supplier`` execution can create a Gmail draft (simulated while
``MARKETMIND_GMAIL_DRY_RUN`` remains true, which is the default).
"""

from __future__ import annotations

import hashlib
import logging

from ..gmail_config import get_gmail_config, live_writes_allowed
from ..schemas import ApprovalRecord, ApprovalStatus

log = logging.getLogger(__name__)


def _assert_approved(approval: ApprovalRecord) -> None:
    if approval.status != ApprovalStatus.APPROVED:
        raise ValueError(
            f"Approval {approval.approval_id!r} is not approved "
            f"(status={approval.status.value})"
        )


def create_supplier_gmail_draft(
    *,
    approval: ApprovalRecord,
    to_address: str,
    subject: str,
    body: str,
    supplier_name: str = "",
) -> dict:
    """Create a supplier outreach draft in Gmail (or simulate).

    Never logs refresh tokens or client secrets.
    """
    if not subject.strip() or not body.strip():
        raise ValueError("subject and body are required")

    _assert_approved(approval)
    cfg = get_gmail_config()

    if not cfg.enabled:
        raise ValueError(
            "Gmail integration is disabled. Set MARKETMIND_GMAIL_ENABLED=true "
            "or run contact_supplier with dry_run=True for file export."
        )
    if not cfg.wired:
        raise ValueError(
            "Gmail is enabled but not configured. Set GMAIL_CLIENT_ID and "
            "GMAIL_REFRESH_TOKEN, or use dry_run=True."
        )

    to = to_address.strip() or "<supplier email>"

    if cfg.dry_run:
        digest = hashlib.sha256(approval.approval_id.encode()).hexdigest()[:12]
        draft_id = f"sim_gmail_{digest}"
        log.info(
            "gmail draft simulated",
            extra={"approval_id": approval.approval_id, "draft_id": draft_id},
        )
        return {
            "kind": "gmail_draft",
            "simulated": True,
            "gmail_draft_id": draft_id,
            "message": "Gmail draft simulated — no API call made.",
            "to": to,
            "subject": subject.strip(),
            "supplier_name": supplier_name.strip(),
        }

    if not live_writes_allowed():
        raise ValueError(
            "Live Gmail writes are blocked (MARKETMIND_ENABLE_LIVE_WRITES=false). "
            "Keep MARKETMIND_GMAIL_DRY_RUN=true or enable live writes explicitly."
        )

    raise ValueError(
        "Live Gmail API is not wired yet. Keep MARKETMIND_GMAIL_DRY_RUN=true "
        "to simulate draft creation after approval."
    )
