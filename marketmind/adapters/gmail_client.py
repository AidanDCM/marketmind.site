"""Gmail draft client — simulated by default; live drafts via Gmail API.

When ``MARKETMIND_GMAIL_ENABLED`` is true and credentials are set, approved
``contact_supplier`` execution can create a Gmail draft (simulated while
``MARKETMIND_GMAIL_DRY_RUN`` remains true, which is the default).

Live draft creation uses OAuth refresh + Gmail ``users.drafts.create``.
Credentials are never logged.
"""

from __future__ import annotations

import base64
import hashlib
import logging
from email.message import EmailMessage
from typing import Any

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from ..gmail_config import GmailConfig, get_gmail_config, live_writes_allowed
from ..schemas import ApprovalRecord, ApprovalStatus

_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
_TIMEOUT = 15.0
log = logging.getLogger(__name__)


def _is_server_error(exc: BaseException) -> bool:
    return isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code >= 500


def _assert_approved(approval: ApprovalRecord) -> None:
    if approval.status != ApprovalStatus.APPROVED:
        raise ValueError(
            f"Approval {approval.approval_id!r} is not approved "
            f"(status={approval.status.value})"
        )


def _encode_raw_message(*, to_address: str, subject: str, body: str, from_email: str = "") -> str:
    msg = EmailMessage()
    if from_email.strip():
        msg["From"] = from_email.strip()
    if to_address.strip() and to_address.strip() != "<supplier email>":
        msg["To"] = to_address.strip()
    msg["Subject"] = subject.strip()
    msg.set_content(body.strip())
    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return encoded.rstrip("=")


class GmailClient:
    """Thin Gmail REST client using a long-lived OAuth refresh token."""

    def __init__(self, config: GmailConfig) -> None:
        if not config.client_id or not config.refresh_token:
            raise ValueError("Gmail client_id and refresh_token are required")
        self._config = config

    @classmethod
    def from_env(cls) -> GmailClient:
        return cls(get_gmail_config())

    @retry(
        retry=retry_if_exception(_is_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _post(
        self,
        url: str,
        *,
        headers: dict[str, str],
        data: dict[str, str] | None = None,
        json_body: dict | None = None,
    ) -> dict[str, Any]:
        log.debug("gmail POST", extra={"host": httpx.URL(url).host})
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(url, headers=headers, data=data, json=json_body)
        resp.raise_for_status()
        return resp.json()

    def refresh_access_token(self) -> str:
        if not self._config.client_secret:
            raise ValueError("GMAIL_CLIENT_SECRET is required for live Gmail API access")
        payload = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": self._config.refresh_token,
            "grant_type": "refresh_token",
        }
        data = self._post(
            _OAUTH_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=payload,
        )
        token = str(data.get("access_token", "")).strip()
        if not token:
            raise ValueError("Gmail token refresh did not return an access_token")
        return token

    def create_draft(self, *, to_address: str, subject: str, body: str) -> dict[str, Any]:
        access_token = self.refresh_access_token()
        raw = _encode_raw_message(
            to_address=to_address,
            subject=subject,
            body=body,
            from_email=self._config.operator_email,
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        return self._post(
            f"{_GMAIL_API_BASE}/users/me/drafts",
            headers=headers,
            json_body={"message": {"raw": raw}},
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
    if not cfg.client_secret:
        raise ValueError(
            "GMAIL_CLIENT_SECRET is required for live Gmail draft creation. "
            "Set it in the environment or keep MARKETMIND_GMAIL_DRY_RUN=true."
        )

    client = GmailClient(cfg)
    api_result = client.create_draft(to_address=to, subject=subject, body=body)
    draft_id = str(api_result.get("id", "")).strip()
    log.info(
        "gmail draft created",
        extra={"approval_id": approval.approval_id, "draft_id": draft_id},
    )
    return {
        "kind": "gmail_draft",
        "simulated": False,
        "gmail_draft_id": draft_id,
        "message": "Gmail draft created — review and send manually from your inbox.",
        "to": to,
        "subject": subject.strip(),
        "supplier_name": supplier_name.strip(),
    }
