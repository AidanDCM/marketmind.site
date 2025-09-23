"""Security tests for the configuration system."""

import re
from unittest.mock import MagicMock, patch

import pytest

from packages.shared.config.loader import load_secrets_from_manager
from packages.shared.config.redact import redact_sensitive_data
from packages.shared.config.schema import DatabaseSettings


def test_no_secrets_in_code():
    """Ensure no hardcoded secrets in the codebase."""
    # List of sensitive patterns to check for
    sensitive_patterns = [
        r'password\s*[=:]\s*[\'"].+[\'"]',
        r'api[_\-]?key\s*[=:]\s*[\'"].+[\'"]',
        r'secret\s*[=:]\s*[\'"].+[\'"]',
        r'token\s*[=:]\s*[\'"].+[\'"]',
        r'aws[_\-]?access[_\-]?key[_\-]?id\s*[=:]\s*[\'"].+[\'"]',
        r'aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*[\'"].+[\'"]',
        r'client[_\-]?id\s*[=:]\s*[\'"].+[\'"]',
        r'client[_\-]?secret\s*[=:]\s*[\'"].+[\'"]',
        r'refresh[_\-]?token\s*[=:]\s*[\'"].+[\'"]',
    ]

    # Check for hardcoded AWS keys (even if they're test/example keys)
    aws_key_pattern = r"(AKIA|ASIA)[A-Z0-9]{16}"

    # This is a simplified check - in a real project, you'd want to scan the entire codebase
    # For this test, we'll just check that our example files don't contain hardcoded secrets
    test_files = [
        "packages/shared/config/schema.py",
        "packages/shared/config/loader.py",
        "packages/shared/config/flags.py",
        "packages/shared/config/redact.py",
        "packages/shared/tests/unit/test_schema.py",
        "packages/shared/tests/unit/test_loader.py",
        "packages/shared/tests/unit/test_flags.py",
        "packages/shared/tests/unit/test_redact.py",
        "packages/shared/tests/integration/test_config_integration.py",
    ]

    for file_path in test_files:
        with open(file_path, "r") as f:
            content = f.read()

            # Check for sensitive patterns
            for pattern in sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Skip if the value is empty or just whitespace
                    if not match or not match.strip() or "***" in match:
                        continue
                    # Skip if it's in a test case (where we might have example values)
                    if "test_" in file_path or "test_" in content:
                        continue
                    raise AssertionError(
                        f"Potential hardcoded secret found in {file_path}: {match}"
                    )

            # Check for AWS keys
            aws_matches = re.findall(aws_key_pattern, content)
            for match in aws_matches:
                # Skip if it's in a test case or example
                if "test_" in file_path or "example" in content.lower():
                    continue
                raise AssertionError(f"Potential AWS key found in {file_path}: {match}")


def test_redaction_patterns():
    """Test that sensitive data patterns are properly redacted."""
    # Test each pattern in the redaction patterns
    test_cases = [
        ("api_key=abc123", "api_key=***REDACTED***"),
        ("password=s3cr3t", "password=***REDACTED***"),
        ("token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token=***REDACTED***"),
        ("aws_secret_key=AKIAIOSFODNN7EXAMPLE", "aws_secret_key=***REDACTED***"),
        ("client_secret=abc123", "client_secret=***REDACTED***"),
        ("refresh_token=abc123", "refresh_token=***REDACTED***"),
    ]

    for input_str, expected in test_cases:
        assert redact_sensitive_data(input_str) == expected, f"Failed to redact: {input_str}"


def test_sensitive_fields_not_logged(caplog):
    """Test that sensitive fields are not logged in plain text."""
    import logging

    from packages.shared.config.redact import setup_redaction

    # Configure logging
    logger = logging.getLogger("test_security_logger")
    logger.setLevel(logging.INFO)

    # Add a handler with redaction
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    setup_redaction(logger)
    logger.addHandler(handler)

    # Log sensitive data
    sensitive_data = {
        "api_key": "abc123",
        "password": "s3cr3t",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "client_secret": "client-secret-123",
        "refresh_token": "refresh-token-123",
        "safe_field": "this is safe",
    }

    # Convert to string to simulate logging
    log_message = str(sensitive_data)
    logger.info(log_message)

    # Check that sensitive data was redacted
    log_output = caplog.text
    assert "abc123" not in log_output
    assert "s3cr3t" not in log_output
    assert "eyJhbGciOiJ" not in log_output  # Part of the JWT
    assert "client-secret-123" not in log_output
    assert "refresh-token-123" not in log_output

    # Check that non-sensitive data is still present
    assert "this is safe" in log_output
    assert "***REDACTED***" in log_output


def test_secrets_not_in_error_messages():
    """Test that secrets are not leaked in error messages."""
    # This would be tested by intentionally causing validation errors
    # and checking that the error messages don't contain sensitive data

    # Test with invalid database URL (should not include the password in the error)
    with pytest.raises(ValueError) as excinfo:
        DatabaseSettings(url="postgresql://user:password@localhost:5432/db")

    error_message = str(excinfo.value).lower()
    assert "password" not in error_message
    assert "***" in error_message  # Should be redacted


@patch("boto3.client")
def test_secrets_manager_ssl_verification(mock_boto):
    """Test that SSL verification is enforced when calling AWS Secrets Manager."""
    # Configure the mock
    mock_client = MagicMock()
    mock_boto.return_value = mock_client

    # Call the function that uses boto3
    load_secrets_from_manager("test-secret")

    # Get the boto3 client call arguments
    args, kwargs = mock_boto.call_args

    # Check that SSL verification is enabled (the default)
    assert "verify" not in kwargs or kwargs["verify"] is True


def test_default_passwords_not_allowed():
    """Test that default passwords are not allowed in production."""
    # In a real test, you would scan configuration files and code for default passwords
    # This is a simplified example

    # List of common default passwords to check for
    default_passwords = [
        "admin",
        "password",
        "123456",
        "qwerty",
        "letmein",
        "welcome",
        "changeme",
        "password1",
        "admin123",
        "welcome123",
    ]

    # This would be a list of files to check in a real test
    files_to_check = [
        "packages/shared/config/schema.py",
        "packages/shared/config/loader.py",
        "packages/shared/tests/unit/test_schema.py",
        "packages/shared/tests/unit/test_loader.py",
    ]

    for file_path in files_to_check:
        with open(file_path, "r") as f:
            content = f.read().lower()
            for pwd in default_passwords:
                # Skip if the password is part of a larger word
                pattern = r"(\b|_|\")" + re.escape(pwd) + r"(\b|_|\")"
                if re.search(pattern, content):
                    # Check if it's in a comment or test case
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if pwd in line.lower():
                            # Skip comments and test cases
                            if not line.strip().startswith("#") and "test_" not in line:
                                raise AssertionError(
                                    f"Default password found in {file_path}, line {i+1}: {pwd}"
                                )
