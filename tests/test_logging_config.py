"""Slice 14: Structured logging tests."""

import json
import logging

import pytest

from marketmind.logging_config import get_logger, mask_secret, setup_logging


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset root logger after each test."""
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def test_setup_logging_installs_handler():
    setup_logging(level="DEBUG")
    root = logging.getLogger()
    assert len(root.handlers) >= 1


def test_setup_logging_idempotent():
    setup_logging()
    setup_logging()
    assert len(logging.getLogger().handlers) == 1


def test_get_logger_returns_logger():
    log = get_logger("test.module")
    assert isinstance(log, logging.Logger)
    assert log.name == "test.module"


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def test_log_output_is_valid_json(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(level="DEBUG", log_file=log_file)
    log = get_logger("json_test")
    log.info("hello world")

    with open(log_file) as f:
        line = f.readline().strip()
    record = json.loads(line)
    assert record["msg"] == "hello world"
    assert record["level"] == "INFO"
    assert "ts" in record


def test_log_includes_extra_fields(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(level="DEBUG", log_file=log_file)
    log = get_logger("extra_test")
    log.info("scored", extra={"score": 0.72, "product": "Kit"})

    with open(log_file) as f:
        record = json.loads(f.readline())
    assert record["score"] == 0.72
    assert record["product"] == "Kit"


# ---------------------------------------------------------------------------
# Secret masking
# ---------------------------------------------------------------------------


def test_mask_secret_masks_stripe_live_key():
    result = mask_secret("key is sk_live_abc123xyz")
    assert "sk_live_abc123xyz" not in result
    assert "***REDACTED***" in result


def test_mask_secret_masks_stripe_test_key():
    result = mask_secret("sk_test_somethinglong123")
    assert "sk_test_" not in result


def test_mask_secret_masks_publishable_key():
    result = mask_secret("pk_live_abc123")
    assert "pk_live_abc123" not in result


def test_mask_secret_masks_webhook_secret():
    result = mask_secret("whsec_abc123def==")
    assert "whsec_" not in result


def test_mask_secret_masks_shopify_token():
    result = mask_secret("shpat_abcdef123456")
    assert "shpat_" not in result


def test_mask_secret_leaves_plain_text_intact():
    plain = "no secrets here, just a product name"
    assert mask_secret(plain) == plain


def test_log_masks_secrets_in_message(tmp_path):
    log_file = str(tmp_path / "test.log")
    setup_logging(level="DEBUG", log_file=log_file)
    log = get_logger("secret_test")
    log.warning("got key sk_live_SUPERSECRET123")

    with open(log_file) as f:
        line = f.read()
    assert "sk_live_SUPERSECRET123" not in line
    assert "***REDACTED***" in line
