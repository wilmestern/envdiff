"""Split an env mapping into multiple named subsets by prefix or key list."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class EnvSplit:
    """A named subset of an environment mapping."""

    name: str
    data: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"EnvSplit(name={self.name!r}, keys={len(self.data)})"

    def as_dict(self) -> dict:
        return {"name": self.name, "keys": sorted(self.data.keys()), "data": dict(self.data)}


def split_by_prefixes(
    env: Dict[str, str],
    prefixes: List[str],
    *,
    case_sensitive: bool = False,
    remainder_name: Optional[str] = "other",
) -> List[EnvSplit]:
    """Partition *env* into one bucket per prefix plus an optional remainder.

    Each key is assigned to the **first** matching prefix.  Keys that match no
    prefix land in the remainder bucket (when *remainder_name* is not None).
    """
    buckets: Dict[str, Dict[str, str]] = {p: {} for p in prefixes}
    remainder: Dict[str, str] = {}

    for key, value in env.items():
        cmp_key = key if case_sensitive else key.upper()
        matched = False
        for prefix in prefixes:
            cmp_prefix = prefix if case_sensitive else prefix.upper()
            if cmp_key.startswith(cmp_prefix):
                buckets[prefix][key] = value
                matched = True
                break
        if not matched:
            remainder[key] = value

    splits: List[EnvSplit] = [EnvSplit(name=p, data=buckets[p]) for p in prefixes]
    if remainder_name is not None:
        splits.append(EnvSplit(name=remainder_name, data=remainder))
    return splits


def split_by_keys(
    env: Dict[str, str],
    groups: Dict[str, List[str]],
    *,
    remainder_name: Optional[str] = "other",
) -> List[EnvSplit]:
    """Partition *env* into named groups defined by explicit key lists.

    Keys absent from all groups land in the remainder bucket.
    """
    assigned: set = set()
    splits: List[EnvSplit] = []

    for name, keys in groups.items():
        data = {k: env[k] for k in keys if k in env}
        assigned.update(data.keys())
        splits.append(EnvSplit(name=name, data=data))

    if remainder_name is not None:
        remainder = {k: v for k, v in env.items() if k not in assigned}
        splits.append(EnvSplit(name=remainder_name, data=remainder))

    return splits
