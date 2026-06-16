"""Landing-page and offer spec generator for MarketMind Autopilot (Slice 5).

Produces a Codex-ready OfferSpec from operator-supplied OfferContext inputs.
All generation is deterministic and template-based. No LLM is called.

Safety rules enforced here:
- No guaranteed results are written.
- No fake urgency, fake scarcity, or countdown timers.
- No fake reviews or testimonials.
- No misleading product claims.
- All claims in the output must derive from operator inputs.
- The safety_flags field names what Codex must NOT build onto the page.

Parts & Pieces reuse note (ADR-0002): RunOnceChain was evaluated but not used.
The spec sections are independent (all generated from the same fixed OfferContext
input, not chained), so a sequential pipeline adds indirection without benefit.
"""

from __future__ import annotations

from .schemas import (
    AnalyticsEvent,
    BundleItem,
    FaqItem,
    OfferContext,
    OfferSpec,
)

# These are the standard e-commerce analytics events every validation page needs.
_STANDARD_EVENTS: list[tuple[str, str, tuple[str, ...]]] = [
    ("page_view", "user lands on the page", ("product_name", "source", "medium")),
    ("scroll_50", "user scrolls past 50% of the page", ("product_name",)),
    ("add_to_cart_click", "user clicks the primary CTA / buy button", ("product_name", "price")),
    ("checkout_start", "user reaches the checkout or payment page", ("product_name", "price")),
    ("purchase", "order is confirmed", ("product_name", "price", "order_id")),
    ("faq_expand", "user opens an FAQ item", ("question",)),
]

# Trust signals that are honest and always appropriate.
_BASE_TRUST_SIGNALS = (
    "Clear product description with no exaggerated claims",
    "Transparent shipping timeline",
    "Stated return and refund policy",
    "Secure checkout badge",
)

# What Codex must never add to the page.
_SAFETY_FLAGS = (
    "no_fake_reviews_or_testimonials",
    "no_guaranteed_results_claims",
    "no_fake_urgency_or_countdown_timers",
    "no_fake_scarcity_banners",
    "no_hidden_shipping_fees",
    "no_misleading_before_after_claims",
    "no_auto_enroll_subscriptions",
)


def generate_offer_spec(ctx: OfferContext) -> OfferSpec:
    """Generate a Codex-ready landing-page spec from operator-supplied context."""

    headline = _headline(ctx)
    subheadline = _subheadline(ctx)
    bundle_items = _bundle_items(ctx)
    faq = _faq(ctx)
    cta_primary, cta_button_label = _cta(ctx)
    analytics_events = _analytics_events()
    trust_signals = _trust_signals(ctx)
    codex_build_notes = _codex_build_notes(ctx)

    return OfferSpec(
        product_name=ctx.product_name,
        headline=headline,
        subheadline=subheadline,
        bundle_items=tuple(bundle_items),
        faq=tuple(faq),
        cta_primary=cta_primary,
        cta_button_label=cta_button_label,
        analytics_events=tuple(analytics_events),
        trust_signals=tuple(trust_signals),
        codex_build_notes=codex_build_notes,
        safety_flags=_SAFETY_FLAGS,
    )


def _headline(ctx: OfferContext) -> str:
    return f"{ctx.key_benefit} — {ctx.product_name}"


def _subheadline(ctx: OfferContext) -> str:
    return (
        f"Designed for {ctx.target_customer}. "
        f"Everything you need, shipped together."
    )


def _bundle_items(ctx: OfferContext) -> list[BundleItem]:
    # The primary item is always included.
    items = [BundleItem(
        name=ctx.product_name,
        description=ctx.key_benefit,
    )]
    # Secondary benefits become companion bundle items.
    for i, benefit in enumerate(ctx.secondary_benefits, start=1):
        items.append(BundleItem(
            name=f"Bonus item {i}",
            description=benefit,
        ))
    return items


def _faq(ctx: OfferContext) -> list[FaqItem]:
    faq: list[FaqItem] = []

    # Address each operator-supplied objection.
    for objection in ctx.common_objections:
        faq.append(FaqItem(
            question=objection,
            answer="[Operator: add an honest answer to this objection here.]",
        ))

    # Always include shipping and return FAQ items if context was supplied.
    if ctx.shipping_note:
        faq.append(FaqItem(
            question="When will my order arrive?",
            answer=ctx.shipping_note,
        ))
    if ctx.return_policy:
        faq.append(FaqItem(
            question="What is your return policy?",
            answer=ctx.return_policy,
        ))

    # Standard safety FAQ item — always present.
    faq.append(FaqItem(
        question="Is this product right for me?",
        answer=(
            f"This kit is designed for {ctx.target_customer}. "
            "If you have specific requirements, contact us before ordering."
        ),
    ))

    return faq


def _cta(ctx: OfferContext) -> tuple[str, str]:
    price_str = f"${ctx.sale_price:.2f}"
    primary = (
        f"Get the {ctx.product_name} for {price_str}. "
        "No subscriptions, no hidden fees."
    )
    button_label = f"Order Now — {price_str}"
    return primary, button_label


def _analytics_events() -> list[AnalyticsEvent]:
    return [
        AnalyticsEvent(name=name, trigger=trigger, properties=props)
        for name, trigger, props in _STANDARD_EVENTS
    ]


def _trust_signals(ctx: OfferContext) -> tuple[str, ...]:
    signals = list(_BASE_TRUST_SIGNALS)
    if ctx.return_policy:
        signals.append(f"Return policy: {ctx.return_policy}")
    if ctx.shipping_note:
        signals.append(f"Shipping: {ctx.shipping_note}")
    return tuple(signals)


def _codex_build_notes(ctx: OfferContext) -> str:
    lines = [
        f"Build a single-product validation landing page for: {ctx.product_name}",
        f"Target customer: {ctx.target_customer}",
        f"Sale price: ${ctx.sale_price:.2f} (display clearly, no hidden fees)",
        "",
        "Required sections (in order):",
        "  1. Hero — headline + subheadline + primary CTA button",
        "  2. What's included — bundle items list",
        "  3. FAQ — all FAQ items from the spec",
        "  4. Trust signals — return policy, shipping, secure checkout",
        "  5. Footer CTA — repeat the buy button",
        "",
        "Required analytics — fire all events from the analytics_events list.",
        "",
        "Hard rules (see safety_flags — these are non-negotiable):",
        "  - No fake reviews or testimonials",
        "  - No guaranteed results",
        "  - No countdown timers or fake scarcity",
        "  - No hidden shipping fees",
        "  - No auto-enroll subscriptions",
        "",
        "Checkout: link the CTA to the approved Stripe Payment Link.",
        "The Payment Link must be created and approved before the page goes live.",
        "Do not hard-code any price on the checkout side — use the Payment Link.",
    ]
    return "\n".join(lines)
