"""Formatters for rendering DiffResult output."""

from typing import List

from envdiff.differ import DiffEntry, DiffResult, DiffStatus

_STATUS_SYMBOL = {
    DiffStatus.ADDED: "+",
    DiffStatus.REMOVED: "-",
    DiffStatus.CHANGED: "~",
    DiffStatus.UNCHANGED: " ",
}

_STATUS_LABEL = {
    DiffStatus.ADDED: "ADDED",
    DiffStatus.REMOVED: "REMOVED",
    DiffStatus.CHANGED: "CHANGED",
    DiffStatus.UNCHANGED: "UNCHANGED",
}


def _format_entry_text(entry: DiffEntry) -> str:
    symbol = _STATUS_SYMBOL[entry.status]
    if entry.status == DiffStatus.ADDED:
        return f"{symbol} {entry.key}={entry.right_value}"
    if entry.status == DiffStatus.REMOVED:
        return f"{symbol} {entry.key}={entry.left_value}"
    if entry.status == DiffStatus.CHANGED:
        return f"{symbol} {entry.key}: {entry.left_value!r} -> {entry.right_value!r}"
    return f"{symbol} {entry.key}={entry.left_value}"


def format_text(result: DiffResult) -> str:
    """Render a DiffResult as a human-readable unified-diff-style string."""
    if not result.entries:
        return "No differences found."
    lines: List[str] = []
    for entry in result.entries:
        lines.append(_format_entry_text(entry))
    summary_parts = []
    if result.added:
        summary_parts.append(f"{len(result.added)} added")
    if result.removed:
        summary_parts.append(f"{len(result.removed)} removed")
    if result.changed:
        summary_parts.append(f"{len(result.changed)} changed")
    if summary_parts:
        lines.append("")
        lines.append("Summary: " + ", ".join(summary_parts))
    return "\n".join(lines)


def format_json(result: DiffResult) -> dict:
    """Render a DiffResult as a JSON-serialisable dictionary."""
    return {
        "has_differences": result.has_differences,
        "summary": {
            "added": len(result.added),
            "removed": len(result.removed),
            "changed": len(result.changed),
            "unchanged": len(result.unchanged),
        },
        "entries": [
            {
                "key": e.key,
                "status": e.status.value,
                "left_value": e.left_value,
                "right_value": e.right_value,
            }
            for e in result.entries
        ],
    }
