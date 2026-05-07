"""High-level summary helpers for diff results, combining differ and reporter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, DiffStatus
from envdiff.reporter import DiffSummary, summarize


@dataclass
class GroupedDiffSummary:
    """Diff summary broken down by key prefix."""

    name_left: str
    name_right: str
    total_added: int
    total_removed: int
    total_changed: int
    total_unchanged: int
    by_prefix: Dict[str, DiffSummary] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return (self.total_added + self.total_removed + self.total_changed) > 0

    def as_dict(self) -> dict:
        return {
            "name_left": self.name_left,
            "name_right": self.name_right,
            "total_added": self.total_added,
            "total_removed": self.total_removed,
            "total_changed": self.total_changed,
            "total_unchanged": self.total_unchanged,
            "has_differences": self.has_differences,
            "by_prefix": {
                prefix: summary.as_dict()
                for prefix, summary in self.by_prefix.items()
            },
        }


def _extract_prefix(key: str, sep: str = "_") -> str:
    """Return the first segment of a key before the separator."""
    parts = key.split(sep, 1)
    return parts[0] if len(parts) > 1 else "__other__"


def grouped_diff_summary(
    result: DiffResult,
    name_left: str = "left",
    name_right: str = "right",
    sep: str = "_",
) -> GroupedDiffSummary:
    """Compute an overall and per-prefix diff summary from a DiffResult."""
    overall: DiffSummary = summarize(result)

    prefix_buckets: Dict[str, List] = {}
    for entry in result.entries:
        prefix = _extract_prefix(entry.key, sep=sep)
        prefix_buckets.setdefault(prefix, [])
        prefix_buckets[prefix].append(entry)

    by_prefix: Dict[str, DiffSummary] = {}
    for prefix, entries in sorted(prefix_buckets.items()):
        sub_result = DiffResult(entries=entries)
        by_prefix[prefix] = summarize(sub_result)

    return GroupedDiffSummary(
        name_left=name_left,
        name_right=name_right,
        total_added=overall.added,
        total_removed=overall.removed,
        total_changed=overall.changed,
        total_unchanged=overall.unchanged,
        by_prefix=by_prefix,
    )


def format_grouped_summary_text(summary: GroupedDiffSummary) -> str:
    """Render a GroupedDiffSummary as a human-readable text block."""
    lines: List[str] = [
        f"Diff: {summary.name_left!r} vs {summary.name_right!r}",
        f"  Added:     {summary.total_added}",
        f"  Removed:   {summary.total_removed}",
        f"  Changed:   {summary.total_changed}",
        f"  Unchanged: {summary.total_unchanged}",
    ]
    if summary.by_prefix:
        lines.append("  By prefix:")
        for prefix, s in summary.by_prefix.items():
            lines.append(
                f"    {prefix:<20} +{s.added} -{s.removed} ~{s.changed} ={s.unchanged}"
            )
    return "\n".join(lines)
