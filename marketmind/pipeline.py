"""Slice 21: offer -> approval pipeline.

The last gap between "score an offer" and "execute an approved action". Given an
OfferContext, this builds the spec, builds the channel payload, creates a gated
approval, and stores the payload in the event ledger — so the operator's only
remaining step is to approve (then the executor runs it).

    OfferContext -> generate_offer_spec -> build channel payload
                 -> make/evaluate approval (HIGH -> PENDING)
                 -> record_action_payload (event ledger)

No money, no external calls: the payload is always built dry-run, and the
approval lands PENDING (never auto-approved). Live execution still requires a
human approval plus credentials at execute time (see executor).
"""

from __future__ import annotations

from sqlalchemy.engine import Engine

from .adapters.shopify_adapter import build_product_draft
from .adapters.stripe_adapter import build_payment_link_payload
from .approvals import evaluate_approval, make_approval_record
from .db import approval_store
from .executor import record_action_payload
from .logging_config import get_logger
from .outreach_drafts import build_supplier_outreach_draft
from .schemas import ApprovalRecord, OfferContext
from .spec_generator import generate_offer_spec

log = get_logger(__name__)

_CHANNEL_ACTION = {
    "stripe": "create_stripe_payment_link",
    "shopify": "publish_shopify_product",
}
_CHANNEL_ROLLBACK = {
    "stripe": "Deactivate the Stripe payment link in the dashboard.",
    "shopify": "Set the Shopify product back to draft / unpublish.",
}


def prepare_offer_for_approval(
    engine: Engine,
    offer_context: OfferContext,
    channel: str = "stripe",
    vendor: str = "MarketMind",
    product_type: str = "",
) -> ApprovalRecord:
    """Turn an OfferContext into a PENDING approval with its payload attached.

    Returns the gated ApprovalRecord (PENDING for the HIGH-risk channel actions).
    Raises ValueError for an unknown channel.
    """
    if channel not in _CHANNEL_ACTION:
        raise ValueError(f"Unknown channel {channel!r}. Use 'stripe' or 'shopify'.")

    spec = generate_offer_spec(offer_context)

    if channel == "stripe":
        payload = build_payment_link_payload(spec)
        summary = (
            f"Create Stripe payment link for {offer_context.product_name} "
            f"at ${offer_context.sale_price:.2f}"
        )
    else:
        payload = build_product_draft(spec, vendor=vendor, product_type=product_type)
        summary = (
            f"Publish Shopify product {offer_context.product_name!r} "
            f"(${offer_context.sale_price:.2f})"
        )

    record = make_approval_record(
        action=_CHANNEL_ACTION[channel],
        summary=summary,
        expected_cost=offer_context.sale_price,
        rollback_plan=_CHANNEL_ROLLBACK[channel],
    )
    gated = evaluate_approval(record)
    approval_store.create_approval(engine, gated)
    record_action_payload(engine, gated.approval_id, payload.to_dict())

    log.info(
        "offer prepared for approval",
        extra={
            "approval_id": gated.approval_id,
            "channel": channel,
            "action": gated.action,
            "status": gated.status.value,
        },
    )
    return gated


def prepare_supplier_outreach_for_approval(
    engine: Engine,
    *,
    supplier_name: str,
    product_name: str,
    sample_quantity: int = 1,
    target_unit_cost: float | None = None,
    operator_note: str = "",
    expected_cost: float = 0.0,
) -> ApprovalRecord:
    """Build a supplier outreach draft and queue a contact_supplier approval."""
    draft = build_supplier_outreach_draft(
        supplier_name=supplier_name,
        product_name=product_name,
        sample_quantity=sample_quantity,
        target_unit_cost=target_unit_cost,
        operator_note=operator_note,
    )
    record = make_approval_record(
        action="contact_supplier",
        summary=f"Contact {supplier_name} about {product_name} sample order",
        expected_cost=expected_cost or (target_unit_cost or 0.0) * sample_quantity,
        rollback_plan="Do not send — discard draft if approval is denied.",
    )
    gated = evaluate_approval(record)
    approval_store.create_approval(engine, gated)
    record_action_payload(engine, gated.approval_id, draft.to_dict())
    log.info(
        "supplier outreach prepared for approval",
        extra={"approval_id": gated.approval_id, "supplier": supplier_name},
    )
    return gated
