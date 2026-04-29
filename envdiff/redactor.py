"""Redaction support for sensitive environment variable values."""

import re
from typing import Optional

DEFAULT_REDACTED = "[REDACTED]"

SENSITIVE_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_\-]?key", re.IGNORECASE),
    re.compile(r"private[_\-]?key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"passphrase", re.IGNORECASE),
]


def is_sensitive(key: str, extra_patterns: Optional[list[str]] = None) -> bool:
    """Return True if the given key name matches any sensitive pattern."""
    patterns = list(SENSITIVE_PATTERNS)
    if extra_patterns:
        patterns.extend(re.compile(p, re.IGNORECASE) for p in extra_patterns)
    return any(pattern.search(key) for pattern in patterns)


def redact_value(
    key: str,
    value: str,
    extra_patterns: Optional[list[str]] = None,
    redacted_placeholder: str = DEFAULT_REDACTED,
) -> str:
    """Return redacted placeholder if key is sensitive, otherwise return value as-is."""
    if is_sensitive(key, extra_patterns):
        return redacted_placeholder
    return value


def redact_env(
    env: dict[str, str],
    extra_patterns: Optional[list[str]] = None,
    redacted_placeholder: str = DEFAULT_REDACTED,
) -> dict[str, str]:
    """Return a copy of the env dict with sensitive values redacted."""
    return {
        key: redact_value(key, value, extra_patterns, redacted_placeholder)
        for key, value in env.items()
    }
