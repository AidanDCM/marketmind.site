"""Slice 51: Gmail-ready outreach draft file export."""

from pathlib import Path

import pytest

from marketmind.gmail_draft import save_outreach_draft_file


def test_save_outreach_draft_file_writes_expected_content(tmp_path: Path):
    path = save_outreach_draft_file(
        approval_id="apr_test_1",
        subject="Sample order request",
        body="Hello — we'd like to order a sample.",
        supplier_name="Acme Co",
        to_address="buyer@acme.example",
        output_dir=tmp_path,
    )
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Subject: Sample order request" in text
    assert "Acme Co" in text
    assert "buyer@acme.example" in text
    assert "Hello — we'd like to order a sample." in text


def test_save_outreach_draft_rejects_empty_fields(tmp_path: Path):
    with pytest.raises(ValueError, match="approval_id"):
        save_outreach_draft_file(
            approval_id="",
            subject="S",
            body="B",
            output_dir=tmp_path,
        )
    with pytest.raises(ValueError, match="subject"):
        save_outreach_draft_file(
            approval_id="apr_x",
            subject="",
            body="B",
            output_dir=tmp_path,
        )
