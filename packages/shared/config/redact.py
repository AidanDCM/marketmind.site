"""
Sensitive data redaction for logging and error reporting.
Prevents accidental logging of secrets, tokens, and other sensitive data.
"""

import logging
import re
from typing import Any, Dict, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Default redaction patterns for common sensitive data
DEFAULT_REDACTION_PATTERNS = {
    # API keys and tokens
    "api_key": r"(?i)(?:api[_-]?key|apikey)[=: ]*([\w\-]+)",
    "bearer_token": r"(?i)bearer[\s=:]+([\w\-_.]+)",
    "access_token": r"(?i)access[_-]?token[=: ]*([\w\-_.]+)",
    "refresh_token": r"(?i)refresh[_-]?token[=: ]*([\w\-_.]+)",
    "client_secret": r"(?i)client[_-]?secret[=: ]*([\w\-_.]+)",
    "session_id": r"(?i)session[_-]?id[=: ]*([\w\-_.]+)",
    # AWS credentials
    "aws_access_key": r"(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?key)[=: ]*([A-Z0-9]{20})",
    "aws_secret_key": r"(?i)(aws[_-]?secret[_-]?(?:access[_-]?)?key|aws[_-]?secret)[=: ]*([a-zA-Z0-9/\+=]{40})",
    "aws_session_token": r"(?i)(aws[_-]?session[_-]?token|aws[_-]?token)[=: ]*([a-zA-Z0-9/\+=]+)",
    # Database credentials
    "db_password": r"(?i)(?:db[_-]?pass(?:word)?|password|pwd)[=: ]*([^\s&\"\']+)",
    "db_uri": r"(?i)(?:postgres(?:ql)?|mysql|mongodb)://[^:]+:([^@]+)@",
    # OAuth
    "oauth_token": r"(?i)oauth[_-]?token[=: ]*([\w\-_.]+)",
    "auth_code": r"(?i)code[=: ]*([\w\-_.]+)",
    # Common sensitive fields
    "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
    "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b",
    "ssn": r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",
}

# Default redaction mask
DEFAULT_MASK = "***REDACTED***"


class Redactor:
    """Redacts sensitive information from strings and data structures."""

    def __init__(
        self,
        patterns: Optional[Dict[str, str]] = None,
        mask: str = DEFAULT_MASK,
        additional_patterns: Optional[Dict[str, str]] = None,
    ):
        """Initialize the redactor with patterns.

        Args:
            patterns: Dictionary of pattern names to regex patterns.
                     If None, uses DEFAULT_REDACTION_PATTERNS.
            mask: The string to use as a mask for redacted content.
            additional_patterns: Additional patterns to add to the default set.
        """
        self.mask = mask
        self.patterns = patterns or DEFAULT_REDACTION_PATTERNS.copy()

        # Add any additional patterns
        if additional_patterns:
            self.patterns.update(additional_patterns)

        # Compile all patterns
        self.compiled_patterns = {
            name: re.compile(pattern, re.IGNORECASE) for name, pattern in self.patterns.items()
        }

    def redact_string(self, text: str) -> str:
        """Redact sensitive information from a string."""
        if not isinstance(text, str):
            return text

        redacted = text
        for name, pattern in self.compiled_patterns.items():
            try:
                # Replace all matches with the mask
                redacted = pattern.sub(self.mask, redacted)
            except Exception as e:
                logger.warning(f"Error applying redaction pattern '{name}': {e}")
                continue

        return redacted

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact sensitive information from a dictionary."""
        if not isinstance(data, dict):
            return self.redact_string(str(data))

        result = {}
        for key, value in data.items():
            # Redact the key if it matches any patterns
            redacted_key = self.redact_string(str(key))

            # Recursively redact the value
            if isinstance(value, dict):
                result[redacted_key] = self.redact_dict(value)
            elif isinstance(value, (list, tuple)):
                result[redacted_key] = [
                    (
                        self.redact_dict(item)
                        if isinstance(item, dict)
                        else self.redact_string(str(item))
                    )
                    for item in value
                ]
            else:
                result[redacted_key] = self.redact_string(str(value))

        return result

    def redact(self, data: Any) -> Any:
        """Redact sensitive information from any data type."""
        if isinstance(data, dict):
            return self.redact_dict(data)
        elif isinstance(data, (list, tuple)):
            return [self.redact(item) for item in data]
        elif isinstance(data, str):
            return self.redact_string(data)
        else:
            return data


# Global redactor instance with default patterns
_redactor = Redactor()


def redact(text: str) -> str:
    """Redact sensitive information from a string."""
    return _redactor.redact_string(text)


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive information from a dictionary."""
    return _redactor.redact_dict(data)


def redact_sensitive_data(record: logging.LogRecord) -> logging.LogRecord:
    """A logging filter that redacts sensitive data from log records."""
    # Redact the message
    if record.msg and isinstance(record.msg, str):
        record.msg = redact(record.msg)

    # Redact any args that are strings
    if record.args:
        if isinstance(record.args, (list, tuple)):
            record.args = tuple(redact(arg) if isinstance(arg, str) else arg for arg in record.args)
        elif isinstance(record.args, dict):
            record.args = {
                k: redact(v) if isinstance(v, str) else v for k, v in record.args.items()
            }

    return record


def add_redaction_filter(logger: logging.Logger) -> None:
    """Add redaction filter to a logger."""
    for handler in logger.handlers:
        handler.addFilter(redact_sensitive_data)


# Add redaction to the root logger by default
add_redaction_filter(logging.getLogger())
