"""Deduplication of environment variable mappings by value."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DeduplicationResult:
    """Result of a deduplication pass over an env mapping."""

    original_count: int
    deduplicated: Dict[str, str] = field(default_factory=dict)
    removed_keys: List[str] = field(default_factory=list)
    value_groups: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def removed_count(self) -> int:
        return len(self.removed_keys)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.removed_keys)

    def as_dict(self) -> dict:
        return {
            "original_count": self.original_count,
            "deduplicated_count": len(self.deduplicated),
            "removed_count": self.removed_count,
            "removed_keys": sorted(self.removed_keys),
            "value_groups": {
                v: sorted(keys)
                for v, keys in self.value_groups.items()
                if len(keys) > 1
            },
        }

    def __repr__(self) -> str:
        return (
            f"DeduplicationResult(original={self.original_count}, "
            f"removed={self.removed_count})"
        )


def deduplicate_env(
    env: Dict[str, str],
    keep: str = "first",
) -> DeduplicationResult:
    """Remove keys that share an identical value with an earlier key.

    Args:
        env: Mapping of env variable names to values.
        keep: Strategy for which key to retain when duplicates are found.
              ``'first'`` keeps the key encountered first (alphabetically
              by key name after sorting); ``'last'`` keeps the final one.

    Returns:
        A :class:`DeduplicationResult` describing what was removed.
    """
    # Build value -> [keys] groups
    value_groups: Dict[str, List[str]] = {}
    for key, value in env.items():
        value_groups.setdefault(value, []).append(key)

    removed: List[str] = []
    kept: Dict[str, str] = {}

    for value, keys in value_groups.items():
        sorted_keys = sorted(keys)
        if keep == "last":
            chosen = sorted_keys[-1]
            discarded = sorted_keys[:-1]
        else:
            chosen = sorted_keys[0]
            discarded = sorted_keys[1:]
        kept[chosen] = value
        removed.extend(discarded)

    # Preserve insertion-like ordering from the original dict
    deduplicated = {k: v for k, v in env.items() if k in kept}

    return DeduplicationResult(
        original_count=len(env),
        deduplicated=deduplicated,
        removed_keys=removed,
        value_groups=value_groups,
    )


def format_deduplication_text(result: DeduplicationResult) -> str:
    """Return a human-readable summary of a deduplication result."""
    lines: List[str] = [
        f"Original keys : {result.original_count}",
        f"After dedup   : {len(result.deduplicated)}",
        f"Removed       : {result.removed_count}",
    ]
    if result.has_duplicates:
        lines.append("")
        lines.append("Duplicate groups (value -> kept_key [removed...]):")
        for value, keys in sorted(result.value_groups.items()):
            if len(keys) < 2:
                continue
            sorted_keys = sorted(keys)
            kept = sorted_keys[0]
            others = ", ".join(sorted_keys[1:])
            preview = value[:40] + "..." if len(value) > 40 else value
            lines.append(f"  [{preview!r}]  kept={kept}  removed={others}")
    return "\n".join(lines)
