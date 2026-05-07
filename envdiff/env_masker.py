"""env_masker.py — Mask environment variable values for safe display or logging.

Provides configurable masking strategies beyond simple redaction:
partial reveal, full mask, and length-preserving mask.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict

from envdiff.redactor import is_sensitive


class MaskStyle(str, Enum):
    FULL = "full"          # Replace entire value with fixed placeholder
    PARTIAL = "partial"    # Show first N chars, mask the rest
    LENGTH = "length"      # Replace each char with mask char (preserves length)


_DEFAULT_PLACEHOLDER = "***"
_DEFAULT_MASK_CHAR = "*"
_DEFAULT_REVEAL_CHARS = 4


def mask_value(
    value: str,
    style: MaskStyle = MaskStyle.FULL,
    placeholder: str = _DEFAULT_PLACEHOLDER,
    mask_char: str = _DEFAULT_MASK_CHAR,
    reveal_chars: int = _DEFAULT_REVEAL_CHARS,
) -> str:
    """Return a masked version of *value* using the requested *style*."""
    if not value:
        return value

    if style == MaskStyle.FULL:
        return placeholder

    if style == MaskStyle.LENGTH:
        return mask_char * len(value)

    if style == MaskStyle.PARTIAL:
        if len(value) <= reveal_chars:
            return mask_char * len(value)
        visible = value[:reveal_chars]
        hidden = mask_char * (len(value) - reveal_chars)
        return visible + hidden

    return placeholder  # fallback


def mask_env(
    env: Dict[str, str],
    style: MaskStyle = MaskStyle.FULL,
    placeholder: str = _DEFAULT_PLACEHOLDER,
    mask_char: str = _DEFAULT_MASK_CHAR,
    reveal_chars: int = _DEFAULT_REVEAL_CHARS,
) -> Dict[str, str]:
    """Return a copy of *env* with sensitive values masked.

    Non-sensitive keys are passed through unchanged.
    """
    result: Dict[str, str] = {}
    for key, value in env.items():
        if is_sensitive(key):
            result[key] = mask_value(
                value,
                style=style,
                placeholder=placeholder,
                mask_char=mask_char,
                reveal_chars=reveal_chars,
            )
        else:
            result[key] = value
    return result
