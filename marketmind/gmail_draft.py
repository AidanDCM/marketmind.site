"""Gmail-ready outreach draft export (dry-run; no Gmail API).

Adapted from Parts-and-Pieces `parts/python/gmail_draft_client`.

Writes a plain-text draft file the operator can paste into Gmail or any mail
client. Live Gmail API send is intentionally not wired — contact_supplier
execution stays manual after approval.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DIR = Path("logs/outreach_drafts")


def save_outreach_draft_file(
    *,
    approval_id: str,
    subject: str,
    body: str,
    supplier_name: str = "",
    to_address: str = "",
    output_dir: str | Path = _DEFAULT_DIR,
) -> Path:
    """Write a draft file and return its path. Creates parent dirs if needed."""
    if not approval_id.strip():
        raise ValueError("approval_id must not be empty")
    if not subject.strip():
        raise ValueError("subject must not be empty")
    if not body.strip():
        raise ValueError("body must not be empty")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = approval_id.strip().replace("/", "_")
    path = out_dir / f"{safe_id}.txt"

    header_lines = [
        f"To: {to_address.strip() or '<supplier email>'}",
        f"Subject: {subject.strip()}",
        f"Supplier: {supplier_name.strip() or 'n/a'}",
        f"Approval: {approval_id.strip()}",
        f"Exported: {datetime.now(timezone.utc).isoformat()}",
        "",
        "--- paste below into your email client ---",
        "",
    ]
    path.write_text("\n".join(header_lines) + body.strip() + "\n", encoding="utf-8")
    return path
