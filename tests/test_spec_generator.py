import pytest

from marketmind import OfferContext, generate_offer_spec

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**kwargs) -> OfferContext:
    defaults = dict(
        product_name="Daily Driver Interior Refresh Kit",
        sale_price=59.0,
        key_benefit="Upgrade your car's interior feel without leaving the driveway",
        target_customer="daily commuters and rideshare drivers with older interiors",
        secondary_benefits=("Microfiber cleaning cloth", "Dashboard protectant wipe"),
        common_objections=(
            "Will this fit my car?",
            "Is the quality worth $59?",
        ),
        shipping_note="Ships in 3-5 business days via USPS First Class.",
        return_policy="30-day hassle-free returns — just contact us first.",
        niche="Daily Driver Upgrade Kits",
    )
    defaults.update(kwargs)
    return OfferContext(**defaults)


# ---------------------------------------------------------------------------
# Acceptance criteria: all sections are generated
# ---------------------------------------------------------------------------


def test_headline_contains_key_benefit_and_product_name():
    spec = generate_offer_spec(_ctx())
    assert "Upgrade your car" in spec.headline
    assert "Daily Driver Interior Refresh Kit" in spec.headline


def test_subheadline_mentions_target_customer():
    spec = generate_offer_spec(_ctx())
    assert "commuters" in spec.subheadline or "rideshare" in spec.subheadline


def test_bundle_contains_primary_product():
    spec = generate_offer_spec(_ctx())
    assert any("Daily Driver Interior Refresh Kit" in b.name for b in spec.bundle_items)


def test_bundle_contains_secondary_benefits():
    spec = generate_offer_spec(_ctx())
    descriptions = [b.description for b in spec.bundle_items]
    assert any("Microfiber" in d for d in descriptions)
    assert any("Dashboard" in d for d in descriptions)


def test_faq_addresses_supplied_objections():
    spec = generate_offer_spec(_ctx())
    questions = [item.question for item in spec.faq]
    assert "Will this fit my car?" in questions
    assert "Is the quality worth $59?" in questions


def test_faq_includes_shipping_and_return():
    spec = generate_offer_spec(_ctx())
    questions = [item.question for item in spec.faq]
    assert any("arrive" in q.lower() or "ship" in q.lower() for q in questions)
    assert any("return" in q.lower() for q in questions)


def test_faq_always_includes_suitability_item():
    spec = generate_offer_spec(_ctx())
    assert any("right for me" in item.question.lower() for item in spec.faq)


def test_faq_suitability_answer_mentions_target_customer():
    spec = generate_offer_spec(_ctx())
    suitability = next(i for i in spec.faq if "right for me" in i.question.lower())
    assert "commuters" in suitability.answer or "rideshare" in suitability.answer


def test_cta_shows_price():
    spec = generate_offer_spec(_ctx())
    assert "59.00" in spec.cta_primary or "$59" in spec.cta_primary
    assert "59.00" in spec.cta_button_label or "$59" in spec.cta_button_label


def test_cta_states_no_hidden_fees():
    # The CTA must explicitly tell the buyer there are no hidden fees.
    spec = generate_offer_spec(_ctx())
    assert "no hidden fees" in spec.cta_primary.lower()


def test_standard_analytics_events_are_present():
    spec = generate_offer_spec(_ctx())
    event_names = {e.name for e in spec.analytics_events}
    assert "page_view" in event_names
    assert "add_to_cart_click" in event_names
    assert "purchase" in event_names
    assert "checkout_start" in event_names


def test_analytics_events_have_properties():
    spec = generate_offer_spec(_ctx())
    purchase = next(e for e in spec.analytics_events if e.name == "purchase")
    assert "price" in purchase.properties
    assert "order_id" in purchase.properties


def test_trust_signals_include_return_and_shipping():
    spec = generate_offer_spec(_ctx())
    combined = " ".join(spec.trust_signals).lower()
    assert "return" in combined
    assert "ship" in combined


def test_codex_build_notes_list_required_sections():
    spec = generate_offer_spec(_ctx())
    notes = spec.codex_build_notes
    assert "Hero" in notes
    assert "FAQ" in notes
    assert "Trust" in notes
    assert "analytics" in notes.lower()


def test_codex_build_notes_names_payment_link():
    spec = generate_offer_spec(_ctx())
    assert "Payment Link" in spec.codex_build_notes


# ---------------------------------------------------------------------------
# Safety: prohibited content must be named in safety_flags
# ---------------------------------------------------------------------------


def test_safety_flags_block_fake_reviews():
    spec = generate_offer_spec(_ctx())
    assert "no_fake_reviews_or_testimonials" in spec.safety_flags


def test_safety_flags_block_guaranteed_results():
    spec = generate_offer_spec(_ctx())
    assert "no_guaranteed_results_claims" in spec.safety_flags


def test_safety_flags_block_fake_urgency():
    spec = generate_offer_spec(_ctx())
    assert "no_fake_urgency_or_countdown_timers" in spec.safety_flags


def test_no_invented_claims_in_headline():
    # Headline must only contain content derived from inputs.
    spec = generate_offer_spec(_ctx(
        product_name="Test Kit",
        key_benefit="Simple honest benefit",
    ))
    assert "guarantee" not in spec.headline.lower()
    assert "proven" not in spec.headline.lower()
    assert "Simple honest benefit" in spec.headline


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_no_secondary_benefits_produces_single_bundle_item():
    spec = generate_offer_spec(_ctx(secondary_benefits=()))
    assert len(spec.bundle_items) == 1


def test_no_objections_still_produces_faq():
    spec = generate_offer_spec(_ctx(common_objections=()))
    # Still has shipping, return, and suitability FAQ items.
    assert len(spec.faq) >= 3


def test_no_shipping_note_omits_shipping_faq():
    spec = generate_offer_spec(_ctx(shipping_note="", return_policy="30-day returns."))
    questions = [i.question for i in spec.faq]
    assert not any("arrive" in q.lower() for q in questions)


def test_no_return_policy_omits_return_faq():
    spec = generate_offer_spec(_ctx(return_policy="", shipping_note="Ships in 3 days."))
    questions = [i.question for i in spec.faq]
    assert not any("return policy" in q.lower() for q in questions)


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def test_empty_product_name_is_invalid():
    with pytest.raises(ValueError, match="product_name is required"):
        OfferContext(
            product_name="  ",
            sale_price=59.0,
            key_benefit="A benefit",
            target_customer="someone",
        )


def test_zero_price_is_invalid():
    with pytest.raises(ValueError, match="sale_price must be greater than zero"):
        OfferContext(
            product_name="A Kit",
            sale_price=0.0,
            key_benefit="A benefit",
            target_customer="someone",
        )


def test_empty_key_benefit_is_invalid():
    with pytest.raises(ValueError, match="key_benefit is required"):
        OfferContext(
            product_name="A Kit",
            sale_price=59.0,
            key_benefit="  ",
            target_customer="someone",
        )
