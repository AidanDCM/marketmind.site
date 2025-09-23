"""Unit tests for the redaction module."""

import json
import logging
import re

from packages.shared.config.redact import (
    RedactingFilter,
    RedactingFormatter,
    setup_redaction,
    redact_sensitive_data,
)


def test_redact_sensitive_data():
    """Test the redact_sensitive_data function with various patterns."""
    # Test API key redaction
    assert redact_sensitive_data("api_key=abc123") == "api_key=***REDACTED***"

    # Test JWT token redaction
    jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert redact_sensitive_data(f"token={jwt}") == "token=***REDACTED***"

    # Test AWS key redaction
    aws_key = "AKIAIOSFODNN7EXAMPLE"
    assert redact_sensitive_data(f"aws_key={aws_key}") == "aws_key=***REDACTED***"

    # Test password redaction
    password = "s3cr3tP@ssw0rd"
    assert redact_sensitive_data(f"password={password}") == "password=***REDACTED***"

    # Test credit card number redaction
    cc = "4111-1111-1111-1111"
    assert redact_sensitive_data(f"cc={cc}") == "cc=***REDACTED***"

    # Test that non-sensitive data is not redacted
    assert redact_sensitive_data("user=john_doe") == "user=john_doe"


def test_redact_sensitive_data_with_custom_patterns():
    """Test redaction with custom patterns."""
    custom_patterns = [
        # Match "custom: value" and redact the value part (group 2)
        (re.compile(r"(custom\s*:\s*)(\w+)", re.IGNORECASE),),
    ]

    # Test with default patterns (should not match)
    assert redact_sensitive_data("custom: secret_value") == "custom: secret_value"

    # Test with custom patterns (should match)
    assert (
        redact_sensitive_data("custom: secret_value", custom_patterns) == "custom: ***REDACTED***"
    )


def test_redacting_filter():
    """Test the RedactingFilter class."""
    # Create a test record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="API key is abc123",
        args=(),
        exc_info=None,
    )

    # Apply the filter
    filter = RedactingFilter()
    filtered_record = filter.filter(record)

    # Check that the message was redacted
    assert "abc123" not in filtered_record.msg
    assert "***REDACTED***" in filtered_record.msg


def test_redacting_formatter():
    """Test the RedactingFormatter class."""
    # Create a test record
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="API key is abc123",
        args=(),
        exc_info=None,
    )

    # Create a formatter
    formatter = RedactingFormatter("%(message)s")

    # Format the record
    formatted = formatter.format(record)

    # Check that the message was redacted
    assert "abc123" not in formatted
    assert "***REDACTED***" in formatted


def test_redacting_formatter_with_json():
    """Test the RedactingFormatter with JSON messages."""
    # Create a test record with a JSON message
    message = {
        "api_key": "abc123",
        "user": "john_doe",
        "nested": {"secret": "s3cr3t", "public": "data"},
    }

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=json.dumps(message),
        args=(),
        exc_info=None,
    )

    # Create a formatter
    formatter = RedactingFormatter("%(message)s")

    # Format the record
    formatted = formatter.format(record)

    # Parse the formatted message back to a dict
    formatted_dict = json.loads(formatted)

    # Check that sensitive data was redacted
    assert formatted_dict["api_key"] == "***REDACTED***"
    assert formatted_dict["user"] == "john_doe"  # Not sensitive
    assert formatted_dict["nested"]["secret"] == "***REDACTED***"
    assert formatted_dict["nested"]["public"] == "data"  # Not sensitive


def test_setup_redaction():
    """Test the setup_redaction function."""
    # Create a test logger
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)

    # Add a handler with a formatter
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    # Apply redaction
    setup_redaction(logger)

    # Check that the filter was added
    assert any(isinstance(f, RedactingFilter) for f in logger.filters)

    # Check that the formatter was replaced
    assert isinstance(handler.formatter, RedactingFormatter)


def test_redaction_performance():
    """Test the performance impact of redaction."""
    import timeit

    # A sample log message with sensitive data
    message = """
    User login attempt:
    - username: john_doe
    - password: s3cr3tP@ssw0rd
    - api_key: abc123def456
    - token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
    - credit_card: 4111-1111-1111-1111
    """

    # Time the redaction
    time_taken = timeit.timeit(
        lambda: redact_sensitive_data(message),
        number=1000,  # Run 1000 times for more accurate timing
    )

    # Check that redaction completes in a reasonable time
    # (this is just a sanity check, not a strict performance test)
    assert time_taken < 1.0  # Should be much faster than 1 second for 1000 iterations

    # Verify that all sensitive data was redacted
    redacted = redact_sensitive_data(message)
    assert "s3cr3tP@ssw0rd" not in redacted
    assert "abc123def456" not in redacted
    assert "eyJhbGciOiJ" not in redacted  # Part of the JWT
    assert "4111-1111-1111-1111" not in redacted
    assert "***REDACTED***" in redacted
