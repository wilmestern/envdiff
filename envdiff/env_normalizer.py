"""Normalize environment variable keys and values for consistent comparison."""

from typing import Dict, Optional


def normalize_key(key: str, *, uppercase: bool = True, strip: bool = True) -> str:
    """Normalize an environment variable key.

    Args:
        key: The raw key string.
        uppercase: If True, convert key to uppercase.
        strip: If True, strip surrounding whitespace.

    Returns:
        Normalized key string.
    """
    if strip:
        key = key.strip()
    if uppercase:
        key = key.upper()
    return key


def normalize_value(value: str, *, strip: bool = True, collapse_whitespace: bool = False) -> str:
    """Normalize an environment variable value.

    Args:
        value: The raw value string.
        strip: If True, strip surrounding whitespace.
        collapse_whitespace: If True, replace internal runs of whitespace with a single space.

    Returns:
        Normalized value string.
    """
    if strip:
        value = value.strip()
    if collapse_whitespace:
        import re
        value = re.sub(r'\s+', ' ', value)
    return value


def normalize_env(
    env: Dict[str, str],
    *,
    uppercase_keys: bool = True,
    strip_keys: bool = True,
    strip_values: bool = True,
    collapse_whitespace: bool = False,
    drop_empty_values: bool = False,
) -> Dict[str, str]:
    """Normalize all keys and values in an environment mapping.

    Args:
        env: Raw environment dictionary.
        uppercase_keys: Convert keys to uppercase.
        strip_keys: Strip whitespace from keys.
        strip_values: Strip whitespace from values.
        collapse_whitespace: Collapse internal whitespace in values.
        drop_empty_values: Omit keys whose normalized value is empty.

    Returns:
        New dictionary with normalized keys and values.
    """
    result: Dict[str, str] = {}
    for raw_key, raw_value in env.items():
        key = normalize_key(raw_key, uppercase=uppercase_keys, strip=strip_keys)
        value = normalize_value(
            raw_value, strip=strip_values, collapse_whitespace=collapse_whitespace
        )
        if drop_empty_values and value == "":
            continue
        result[key] = value
    return result


def find_duplicate_keys(env: Dict[str, str]) -> Dict[str, str]:
    """Detect keys that would collide after normalization.

    Returns a mapping of normalized_key -> original_key for any key
    that appears more than once after uppercasing.
    """
    seen: Dict[str, str] = {}
    duplicates: Dict[str, str] = {}
    for raw_key in env:
        normalized = normalize_key(raw_key)
        if normalized in seen:
            duplicates[normalized] = raw_key
        else:
            seen[normalized] = raw_key
    return duplicates
