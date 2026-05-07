"""Utilities for sorting and ordering environment variable mappings."""

from __future__ import annotations

from typing import Dict, List, Optional


def sort_env(
    env: Dict[str, str],
    *,
    reverse: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return a new dict with keys sorted alphabetically.

    Args:
        env: The environment mapping to sort.
        reverse: If True, sort in descending order.
        case_sensitive: If True, uppercase letters sort before lowercase.

    Returns:
        A new ordered dict with keys sorted.
    """
    key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())
    sorted_keys = sorted(env.keys(), key=key_fn, reverse=reverse)
    return {k: env[k] for k in sorted_keys}


def sort_by_prefix(
    env: Dict[str, str],
    priority_prefixes: Optional[List[str]] = None,
    *,
    reverse: bool = False,
) -> Dict[str, str]:
    """Sort keys so that those matching priority prefixes come first.

    Keys matching the first prefix appear before keys matching the second, etc.
    Remaining keys are sorted alphabetically after all priority groups.

    Args:
        env: The environment mapping to sort.
        priority_prefixes: Ordered list of prefix strings to prioritise.
        reverse: If True, reverse the order within each group.

    Returns:
        A new ordered dict.
    """
    prefixes = [p.upper() for p in (priority_prefixes or [])]

    def _group(key: str) -> int:
        upper = key.upper()
        for idx, prefix in enumerate(prefixes):
            if upper.startswith(prefix):
                return idx
        return len(prefixes)

    sorted_keys = sorted(
        env.keys(),
        key=lambda k: (_group(k), k.lower()),
        reverse=reverse,
    )
    return {k: env[k] for k in sorted_keys}


def format_sorted_text(env: Dict[str, str], *, title: str = "") -> str:
    """Render a sorted env mapping as a human-readable text block.

    Args:
        env: Already-sorted (or unsorted) mapping to render.
        title: Optional heading line.

    Returns:
        A multiline string.
    """
    lines: List[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    for key, value in env.items():
        lines.append(f"{key}={value}")
    return "\n".join(lines)
