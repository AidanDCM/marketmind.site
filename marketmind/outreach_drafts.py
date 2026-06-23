"""Supplier outreach draft generator (dry-run; no email API).

Adapted from Parts-and-Pieces `parts/python/gmail_draft_client` — produces draft
text only. Live send requires approval + future Gmail integration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SupplierOutreachDraft:
    supplier_name: str
    product_name: str
    subject: str
    body: str
    dry_run: bool = True

    def to_dict(self) -> dict:
        return {
            "supplier_name": self.supplier_name,
            "product_name": self.product_name,
            "subject": self.subject,
            "body": self.body,
            "dry_run": self.dry_run,
        }


def build_supplier_outreach_draft(
    *,
    supplier_name: str,
    product_name: str,
    sample_quantity: int = 1,
    target_unit_cost: float | None = None,
    operator_note: str = "",
) -> SupplierOutreachDraft:
    """Build a professional sample-order inquiry email draft."""
    if not supplier_name.strip():
        raise ValueError("supplier_name must not be empty")
    if not product_name.strip():
        raise ValueError("product_name must not be empty")
    if sample_quantity < 1:
        raise ValueError("sample_quantity must be >= 1")

    cost_line = ""
    if target_unit_cost is not None and target_unit_cost > 0:
        cost_line = f"\nOur target landed unit cost is around ${target_unit_cost:.2f}."
    note_line = f"\n\nAdditional context: {operator_note.strip()}" if operator_note.strip() else ""

    subject = f"Sample order inquiry — {product_name.strip()}"
    body = (
        f"Hi {supplier_name.strip()},\n\n"
        f"I'm evaluating {product_name.strip()} for a small validation test "
        f"and would like to request {sample_quantity} sample unit(s).\n\n"
        f"Could you please confirm:\n"
        f"- MOQ for a sample order\n"
        f"- Unit price and shipping to the US\n"
        f"- Lead time\n"
        f"- Return policy for defective units{cost_line}"
        f"{note_line}\n\n"
        f"Thank you,\n"
        f"Aidan\n"
        f"MarketMind Autopilot"
    )
    return SupplierOutreachDraft(
        supplier_name=supplier_name.strip(),
        product_name=product_name.strip(),
        subject=subject,
        body=body,
        dry_run=True,
    )
