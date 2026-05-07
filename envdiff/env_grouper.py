"""Group environment variables by prefix or namespace."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvGroup:
    """A named group of environment variable keys."""

    name: str
    keys: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvGroup(name={self.name!r}, keys={len(self.keys)})"

    def as_dict(self) -> dict:
        return {"name": self.name, "keys": sorted(self.keys)}


def group_by_prefix(
    env: Dict[str, str],
    separator: str = "_",
    min_group_size: int = 1,
    ungrouped_label: str = "OTHER",
) -> Dict[str, EnvGroup]:
    """Group keys by their first prefix segment.

    Keys without a separator are placed in the ungrouped_label group.
    Groups smaller than min_group_size are merged into ungrouped_label.
    """
    buckets: Dict[str, List[str]] = defaultdict(list)

    for key in env:
        if separator in key:
            prefix = key.split(separator, 1)[0]
        else:
            prefix = ungrouped_label
        buckets[prefix].append(key)

    groups: Dict[str, EnvGroup] = {}
    ungrouped = EnvGroup(name=ungrouped_label)

    for prefix, keys in buckets.items():
        if prefix == ungrouped_label or len(keys) < min_group_size:
            ungrouped.keys.extend(keys)
        else:
            groups[prefix] = EnvGroup(name=prefix, keys=keys)

    if ungrouped.keys:
        groups[ungrouped_label] = ungrouped

    return groups


def format_groups_text(
    groups: Dict[str, EnvGroup],
    env: Optional[Dict[str, str]] = None,
    redact: bool = False,
) -> str:
    """Render grouped keys as human-readable text."""
    from envdiff.redactor import redact_env

    display_env = redact_env(env) if (env and redact) else (env or {})

    lines: List[str] = []
    for name in sorted(groups):
        group = groups[name]
        lines.append(f"[{name}] ({len(group.keys)} keys)")
        for key in sorted(group.keys):
            if display_env:
                value = display_env.get(key, "")
                lines.append(f"  {key}={value}")
            else:
                lines.append(f"  {key}")
        lines.append("")
    return "\n".join(lines).rstrip()
