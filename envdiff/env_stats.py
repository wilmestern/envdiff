"""Compute statistics over an environment variable set."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.redactor import is_sensitive


@dataclass
class EnvStats:
    """Aggregate statistics for a collection of environment variables."""

    total: int = 0
    sensitive_count: int = 0
    plain_count: int = 0
    empty_value_count: int = 0
    prefixes: Dict[str, int] = field(default_factory=dict)
    longest_key: str = ""
    longest_value_key: str = ""

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "sensitive_count": self.sensitive_count,
            "plain_count": self.plain_count,
            "empty_value_count": self.empty_value_count,
            "prefixes": dict(sorted(self.prefixes.items())),
            "longest_key": self.longest_key,
            "longest_value_key": self.longest_value_key,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvStats(total={self.total}, sensitive={self.sensitive_count}, "
            f"plain={self.plain_count}, empty={self.empty_value_count})"
        )


def compute_stats(env: Dict[str, str]) -> EnvStats:
    """Return an :class:`EnvStats` summarising *env*."""
    stats = EnvStats()
    stats.total = len(env)

    max_key_len = -1
    max_val_len = -1

    for key, value in env.items():
        # Sensitivity
        if is_sensitive(key):
            stats.sensitive_count += 1
        else:
            stats.plain_count += 1

        # Empty values
        if value == "":
            stats.empty_value_count += 1

        # Prefix breakdown (first segment before '_')
        prefix = key.split("_")[0] if "_" in key else key
        stats.prefixes[prefix] = stats.prefixes.get(prefix, 0) + 1

        # Longest key
        if len(key) > max_key_len:
            max_key_len = len(key)
            stats.longest_key = key

        # Key whose value is longest
        if len(value) > max_val_len:
            max_val_len = len(value)
            stats.longest_value_key = key

    return stats


def format_stats_text(stats: EnvStats) -> str:
    """Return a human-readable summary of *stats*."""
    lines: List[str] = [
        f"Total keys       : {stats.total}",
        f"Sensitive keys   : {stats.sensitive_count}",
        f"Plain keys       : {stats.plain_count}",
        f"Empty values     : {stats.empty_value_count}",
        f"Longest key      : {stats.longest_key or '(none)'}",
        f"Longest value key: {stats.longest_value_key or '(none)'}",
        "Prefix breakdown :",
    ]
    for prefix, count in sorted(stats.prefixes.items()):
        lines.append(f"  {prefix}: {count}")
    return "\n".join(lines)
