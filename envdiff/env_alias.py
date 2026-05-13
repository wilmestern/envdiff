"""Resolve and apply key aliases across environment variable sets."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AliasResult:
    """Result of applying alias mappings to an environment dict."""

    original: Dict[str, str]
    resolved: Dict[str, str]
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.applied)

    def as_dict(self) -> dict:
        return {
            "applied": sorted(self.applied),
            "skipped": sorted(self.skipped),
            "resolved_count": len(self.resolved),
        }

    def __repr__(self) -> str:
        return (
            f"AliasResult(applied={len(self.applied)}, "
            f"skipped={len(self.skipped)})"
        )


def apply_aliases(
    env: Dict[str, str],
    aliases: Dict[str, str],
    overwrite: bool = False,
) -> AliasResult:
    """Copy values from alias source keys to canonical target keys.

    Args:
        env: The environment dict to transform.
        aliases: Mapping of {canonical_key: alias_key}.
        overwrite: If True, overwrite existing canonical keys.

    Returns:
        AliasResult with the resolved environment and metadata.
    """
    resolved = dict(env)
    applied: List[str] = []
    skipped: List[str] = []

    for canonical, alias in aliases.items():
        if alias not in env:
            skipped.append(alias)
            continue
        if canonical in resolved and not overwrite:
            skipped.append(canonical)
            continue
        resolved[canonical] = env[alias]
        applied.append(canonical)

    return AliasResult(original=env, resolved=resolved, applied=applied, skipped=skipped)


def invert_aliases(aliases: Dict[str, str]) -> Dict[str, str]:
    """Invert an alias mapping: {canonical: alias} -> {alias: canonical}."""
    return {v: k for k, v in aliases.items()}


def find_unresolved(
    env: Dict[str, str], aliases: Dict[str, str]
) -> List[str]:
    """Return canonical keys whose alias source is missing from env."""
    return [
        canonical
        for canonical, alias in aliases.items()
        if alias not in env and canonical not in env
    ]
