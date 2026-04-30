"""Summary reporter for diff results."""
from dataclasses import dataclass
from typing import Dict

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class DiffSummary:
    """Aggregated statistics for a diff result."""
    total: int
    added: int
    removed: int
    changed: int
    unchanged: int
    redacted: int

    def as_dict(self) -> Dict[str, int]:
        return {
            "total": self.total,
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "unchanged": self.unchanged,
            "redacted": self.redacted,
        }

    def has_differences(self) -> bool:
        """Return True if any meaningful differences exist."""
        return (self.added + self.removed + self.changed) > 0


def summarize(result: DiffResult) -> DiffSummary:
    """Compute a summary of counts from a DiffResult."""
    added = sum(1 for e in result.entries if e.status == DiffStatus.ADDED)
    removed = sum(1 for e in result.entries if e.status == DiffStatus.REMOVED)
    changed = sum(1 for e in result.entries if e.status == DiffStatus.CHANGED)
    unchanged = sum(1 for e in result.entries if e.status == DiffStatus.UNCHANGED)
    redacted = sum(
        1 for e in result.entries
        if e.old_value == "[REDACTED]" or e.new_value == "[REDACTED]"
    )
    total = len(result.entries)
    return DiffSummary(
        total=total,
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
        redacted=redacted,
    )


def format_summary_text(summary: DiffSummary) -> str:
    """Render a human-readable summary block."""
    lines = [
        "--- Summary ---",
        f"  Added:     {summary.added}",
        f"  Removed:   {summary.removed}",
        f"  Changed:   {summary.changed}",
        f"  Unchanged: {summary.unchanged}",
        f"  Redacted:  {summary.redacted}",
        f"  Total:     {summary.total}",
    ]
    if not summary.has_differences():
        lines.append("  (no differences found)")
    return "\n".join(lines)
