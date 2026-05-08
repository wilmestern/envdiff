"""Detect and report duplicate or aliased keys across environment variable sets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class DuplicateReport:
    """Report of duplicate and aliased keys found across one or more env sets."""

    name: str
    exact_duplicates: Dict[str, List[str]] = field(default_factory=dict)
    case_aliases: List[Tuple[str, str]] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return bool(self.exact_duplicates) or bool(self.case_aliases)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "exact_duplicates": self.exact_duplicates,
            "case_aliases": [{"a": a, "b": b} for a, b in self.case_aliases],
            "has_duplicates": self.has_duplicates,
        }

    def __repr__(self) -> str:
        return (
            f"DuplicateReport(name={self.name!r}, "
            f"exact={len(self.exact_duplicates)}, "
            f"aliases={len(self.case_aliases)})"
        )


def find_exact_duplicates(keys: List[str]) -> Dict[str, List[str]]:
    """Return mapping of key -> list of positions where it appears more than once."""
    seen: Dict[str, List[int]] = {}
    for idx, key in enumerate(keys):
        seen.setdefault(key, []).append(idx)
    return {k: positions for k, positions in seen.items() if len(positions) > 1}


def find_case_aliases(env: Dict[str, str]) -> List[Tuple[str, str]]:
    """Return pairs of keys that differ only in case."""
    lower_map: Dict[str, str] = {}
    aliases: List[Tuple[str, str]] = []
    for key in env:
        lower = key.lower()
        if lower in lower_map and lower_map[lower] != key:
            aliases.append((lower_map[lower], key))
        else:
            lower_map[lower] = key
    return aliases


def detect_duplicates(name: str, env: Dict[str, str]) -> DuplicateReport:
    """Analyse *env* and return a DuplicateReport."""
    keys = list(env.keys())
    exact = find_exact_duplicates(keys)
    aliases = find_case_aliases(env)
    return DuplicateReport(name=name, exact_duplicates=exact, case_aliases=aliases)


def format_duplicate_report_text(report: DuplicateReport) -> str:
    """Render a DuplicateReport as a human-readable string."""
    lines: List[str] = [f"Duplicate report for '{report.name}'"]
    if not report.has_duplicates:
        lines.append("  No duplicates or aliases found.")
        return "\n".join(lines)
    if report.exact_duplicates:
        lines.append("  Exact duplicates:")
        for key, positions in sorted(report.exact_duplicates.items()):
            lines.append(f"    {key}: appears at positions {positions}")
    if report.case_aliases:
        lines.append("  Case aliases:")
        for a, b in report.case_aliases:
            lines.append(f"    '{a}' vs '{b}'")
    return "\n".join(lines)
