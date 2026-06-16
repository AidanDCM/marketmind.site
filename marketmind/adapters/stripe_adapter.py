"""Slice 9: Stripe Payment Links adapter — dry-run only.

build_payment_link_payload() converts an OfferSpec into the Stripe Payment Link
request payload. It NEVER calls the Stripe API.

Live creation is gated at two levels:
  1. The ApprovalRecord must have risk_level=HIGH and status=APPROVED.
  2. The caller must explicitly pass dry_run=False.

Even then, this module only returns a validated PaymentLinkPayload dict —
the operator (or a future live execution layer) is responsible for the
actual API call. No secrets are included in the payload or logged anywhere.
"""

from __future__ import annotations

import math

from ..schemas import ApprovalRecord, ApprovalStatus, OfferSpec, PaymentLinkPayload, RiskLevel


def build_payment_link_payload(
    offer_spec: OfferSpec,
    approval: ApprovalRecord | None = None,
    *,
    dry_run: bool = True,
) -> PaymentLinkPayload:
    """Build a Stripe Payment Link payload from an OfferSpec.

    Parameters
    ----------
    offer_spec:
        The spec produced by generate_offer_spec().
    approval:
        An ApprovalRecord that must be HIGH + APPROVED to allow live creation.
        If None (or unapproved), dry_run is forced to True.
    dry_run:
        Explicit opt-out of dry-run mode. Requires a valid approval.

    Returns
    -------
    PaymentLinkPayload
        Always has ``dry_run=True`` unless a valid HIGH+APPROVED record is
        supplied and ``dry_run=False`` is explicitly passed.
    """
    if not offer_spec.product_name.strip():
        raise ValueError("offer_spec.product_name is required")
    if offer_spec.cta_button_label == "" and offer_spec.headline == "":
        raise ValueError("offer_spec must have at least a headline or cta_button_label")

    # Resolve live-mode eligibility.
    live_allowed = (
        approval is not None
        and approval.risk_level == RiskLevel.HIGH
        and approval.status == ApprovalStatus.APPROVED
    )
    effective_dry_run = True if not live_allowed else dry_run

    # Price: extract from spec cta_primary or product_name context.
    # The OfferSpec carries sale_price indirectly via the CTA text; the caller
    # should pass a spec built from an OfferContext that has the sale price.
    # We derive unit_amount_cents from the OfferContext sale_price embedded in
    # the CTA string as a fallback. If unparseable, we require the caller to
    # pass it explicitly via a keyword (kept simple: parse from cta_button_label).
    unit_amount_cents = _extract_price_cents(offer_spec)

    metadata: dict[str, str] = {
        "product_name": offer_spec.product_name,
        "dry_run": str(effective_dry_run).lower(),
    }
    if approval is not None:
        metadata["approval_id"] = approval.approval_id

    return PaymentLinkPayload(
        product_name=offer_spec.product_name,
        unit_amount_cents=unit_amount_cents,
        currency="usd",
        mode="payment",
        metadata=metadata,
        dry_run=effective_dry_run,
    )


def _extract_price_cents(offer_spec: OfferSpec) -> int:
    """Parse price from the CTA button label (e.g. 'Buy Now — $59.00').

    Returns 0 if no price can be parsed; the caller should validate.
    """
    import re

    targets = [offer_spec.cta_button_label, offer_spec.cta_primary, offer_spec.headline]
    for text in targets:
        match = re.search(r"\$(\d+(?:\.\d+)?)", text)
        if match:
            dollars = float(match.group(1))
            return math.floor(dollars * 100)
    return 0
