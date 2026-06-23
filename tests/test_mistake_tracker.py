"""Tests for marketmind.mistake_tracker."""

import pytest

from marketmind.mistake_tracker import (
    JsonlMistakeTracker,
    suggest_mistakes,
)


def test_append_and_list(tmp_path):
    tracker = JsonlMistakeTracker(tmp_path / "mistakes.jsonl")
    record = tracker.append(
        category="cac_too_high",
        experiment_id="exp_001",
        summary="CAC blew past break-even",
        lesson="Pause ads earlier when CAC trends up.",
        tags=["kill"],
    )
    assert record.mistake_id.startswith("mistake-")
    items = tracker.list_mistakes(experiment_id="exp_001")
    assert len(items) == 1
    assert items[0].lesson.startswith("Pause ads")


def test_invalid_category_raises(tmp_path):
    tracker = JsonlMistakeTracker(tmp_path / "mistakes.jsonl")
    with pytest.raises(ValueError, match="category"):
        tracker.append(
            category="not_a_real_category",
            experiment_id="exp_001",
            summary="x",
            lesson="y",
        )


def test_suggest_from_kill_ruling():
    suggestions = suggest_mistakes(
        experiment_id="exp_kill",
        product_name="Widget",
        ruling="kill",
        risks=["estimated_cac_above_break_even"],
    )
    categories = {s.category for s in suggestions}
    assert "cac_too_high" in categories


def test_suggest_from_refund_risk():
    suggestions = suggest_mistakes(
        experiment_id="exp_ref",
        product_name="Widget",
        ruling="continue",
        risks=["refund rate above threshold"],
    )
    assert any(s.category == "high_refunds" for s in suggestions)


def test_suggest_from_notes():
    suggestions = suggest_mistakes(
        experiment_id="exp_note",
        product_name="Widget",
        ruling=None,
        risks=[],
        note_bodies=["Creative fatigue — need new hooks before next spend."],
    )
    assert any(s.source == "auto_ruling" for s in suggestions)
    assert any("Creative fatigue" in s.lesson for s in suggestions)
