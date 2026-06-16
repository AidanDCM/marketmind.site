"""Slice 10: Shopify adapter — read-only / draft only.

build_product_draft() converts an OfferSpec into a Shopify product draft
payload. The returned payload always has status='draft'. It NEVER calls the
Shopify API.

Publishing is gated at two levels:
  1. The ApprovalRecord must have risk_level=HIGH and status=APPROVED.
  2. The caller must explicitly pass dry_run=False.

Even then, this module only returns a validated ProductDraftPayload —
the operator (or a future live execution layer) is responsible for the
actual API call. No secrets are included in the payload or logged anywhere.
"""

from __future__ import annotations

import re

from ..schemas import (
    ApprovalRecord,
    ApprovalStatus,
    OfferSpec,
    ProductDraftPayload,
    RiskLevel,
    ShopifyVariant,
)


def build_product_draft(
    offer_spec: OfferSpec,
    vendor: str = "MarketMind",
    product_type: str = "",
    approval: ApprovalRecord | None = None,
    *,
    dry_run: bool = True,
) -> ProductDraftPayload:
    """Build a Shopify product draft payload from an OfferSpec.

    Parameters
    ----------
    offer_spec:
        The spec produced by generate_offer_spec().
    vendor:
        The Shopify vendor/brand name. Defaults to 'MarketMind'.
    product_type:
        Optional Shopify product_type string (e.g. 'Car Accessories').
    approval:
        An ApprovalRecord that must be HIGH + APPROVED to allow live publishing.
        If None (or unapproved), dry_run is forced to True and status stays 'draft'.
    dry_run:
        Explicit opt-out of dry-run mode. Requires a valid approval.

    Returns
    -------
    ProductDraftPayload
        Always ``status='draft'``. ``dry_run`` is True unless a valid
        HIGH+APPROVED record is supplied and ``dry_run=False`` is passed.
    """
    if not offer_spec.product_name.strip():
        raise ValueError("offer_spec.product_name is required")

    live_allowed = (
        approval is not None
        and approval.risk_level == RiskLevel.HIGH
        and approval.status == ApprovalStatus.APPROVED
    )
    effective_dry_run = True if not live_allowed else dry_run

    body_html = _build_body_html(offer_spec)
    price_str = _extract_price_str(offer_spec)
    tags = _build_tags(offer_spec)

    variant = ShopifyVariant(
        price=price_str,
        sku=_slugify(offer_spec.product_name),
        inventory_management="shopify",
        fulfillment_service="manual",
    )

    return ProductDraftPayload(
        title=offer_spec.product_name,
        body_html=body_html,
        vendor=vendor,
        product_type=product_type or offer_spec.product_name,
        status="draft",
        variants=(variant,),
        tags=tags,
        dry_run=effective_dry_run,
    )


def _build_body_html(offer_spec: OfferSpec) -> str:
    parts: list[str] = [f"<p>{offer_spec.subheadline}</p>"]

    if offer_spec.bundle_items:
        parts.append("<ul>")
        for item in offer_spec.bundle_items:
            parts.append(f"<li><strong>{item.name}</strong> — {item.description}</li>")
        parts.append("</ul>")

    if offer_spec.trust_signals:
        parts.append("<p>" + " | ".join(offer_spec.trust_signals) + "</p>")

    return "\n".join(parts)


def _extract_price_str(offer_spec: OfferSpec) -> str:
    targets = [offer_spec.cta_button_label, offer_spec.cta_primary, offer_spec.headline]
    for text in targets:
        match = re.search(r"\$(\d+(?:\.\d+)?)", text)
        if match:
            dollars = float(match.group(1))
            return f"{dollars:.2f}"
    return "0.00"


def _build_tags(offer_spec: OfferSpec) -> str:
    tags: list[str] = []
    if offer_spec.product_name:
        tags.append(_slugify(offer_spec.product_name))
    tags.append("marketmind-draft")
    return ", ".join(tags)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
