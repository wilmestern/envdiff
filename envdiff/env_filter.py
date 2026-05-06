"""Filter environment variable sets by key patterns or prefixes."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, Iterable, List, Optional


def filter_by_prefix(
    env: Dict[str, str],
    prefixes: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return only keys that start with any of the given prefixes."""
    prefixes = list(prefixes)
    if not prefixes:
        return dict(env)

    def _matches(key: str) -> bool:
        k = key if case_sensitive else key.upper()
        for p in prefixes:
            p_cmp = p if case_sensitive else p.upper()
            if k.startswith(p_cmp):
                return True
        return False

    return {k: v for k, v in env.items() if _matches(k)}


def filter_by_pattern(
    env: Dict[str, str],
    patterns: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return only keys matching any of the given glob patterns."""
    patterns = list(patterns)
    if not patterns:
        return dict(env)

    flags = 0 if case_sensitive else re.IGNORECASE

    def _matches(key: str) -> bool:
        for pat in patterns:
            if fnmatch.fnmatchcase(
                key if case_sensitive else key.upper(),
                pat if case_sensitive else pat.upper(),
            ):
                return True
        return False

    return {k: v for k, v in env.items() if _matches(k)}


def exclude_keys(
    env: Dict[str, str],
    keys: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return env without the specified keys."""
    if case_sensitive:
        drop = set(keys)
        return {k: v for k, v in env.items() if k not in drop}
    drop = {k.upper() for k in keys}
    return {k: v for k, v in env.items() if k.upper() not in drop}


def select_keys(
    env: Dict[str, str],
    keys: Iterable[str],
    *,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return only the specified keys that exist in env."""
    if case_sensitive:
        keep = set(keys)
        return {k: v for k, v in env.items() if k in keep}
    keep = {k.upper() for k in keys}
    return {k: v for k, v in env.items() if k.upper() in keep}
