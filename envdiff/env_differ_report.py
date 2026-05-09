"""Generates a structured diff report combining diff results with stats and metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, DiffStatus
from envdiff.env_stats import EnvStats, compute_stats
from envdiff.reporter import DiffSummary, summarize


@dataclass
class DiffReport:
    """Combined report of a diff operation with summary and per-source stats."""

    left_name: str
    right_name: str
    summary: DiffSummary
    left_stats: EnvStats
    right_stats: EnvStats
    entries: list = field(default_factory=list)
    title: Optional[str] = None

    @property
    def has_differences(self) -> bool:
        return self.summary.has_differences

    def as_dict(self) -> Dict:
        return {
            "title": self.title,
            "left": self.left_name,
            "right": self.right_name,
            "summary": {
                "added": self.summary.added,
                "removed": self.summary.removed,
                "changed": self.summary.changed,
                "unchanged": self.summary.unchanged,
            },
            "left_stats": self.left_stats.as_dict(),
            "right_stats": self.right_stats.as_dict(),
            "has_differences": self.has_differences,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DiffReport(left={self.left_name!r}, right={self.right_name!r}, "
            f"added={self.summary.added}, removed={self.summary.removed}, "
            f"changed={self.summary.changed})"
        )


def build_diff_report(
    result: DiffResult,
    left_env: Dict[str, str],
    right_env: Dict[str, str],
    left_name: str = "left",
    right_name: str = "right",
    title: Optional[str] = None,
) -> DiffReport:
    """Build a DiffReport from a DiffResult and the two source environments."""
    summary = summarize(result)
    left_stats = compute_stats(left_env, name=left_name)
    right_stats = compute_stats(right_env, name=right_name)
    entries = [
        e for e in result.entries if e.status != DiffStatus.UNCHANGED
    ]
    return DiffReport(
        left_name=left_name,
        right_name=right_name,
        summary=summary,
        left_stats=left_stats,
        right_stats=right_stats,
        entries=entries,
        title=title,
    )


def format_diff_report_text(report: DiffReport) -> str:
    """Render a DiffReport as a human-readable text block."""
    lines: List[str] = []
    if report.title:
        lines.append(f"=== {report.title} ===")
    lines.append(f"Comparing: {report.left_name} vs {report.right_name}")
    lines.append(
        f"Summary  : +{report.summary.added} added, "
        f"-{report.summary.removed} removed, "
        f"~{report.summary.changed} changed"
    )
    lines.append(f"Left  stats: {report.left_stats.total_keys} keys, "
                 f"{report.left_stats.sensitive_keys} sensitive")
    lines.append(f"Right stats: {report.right_stats.total_keys} keys, "
                 f"{report.right_stats.sensitive_keys} sensitive")
    if not report.has_differences:
        lines.append("No differences found.")
    return "\n".join(lines)
