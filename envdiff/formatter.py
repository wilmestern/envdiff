"""Formatters for diff output, including optional summary block."""
import json
from typing import Optional

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.reporter import DiffSummary, format_summary_text, summarize

_STATUS_SYMBOL = {
    DiffStatus.ADDED: "+",
    DiffStatus.REMOVED: "-",
    DiffStatus.CHANGED: "~",
    DiffStatus.UNCHANGED: " ",
}


def _format_entry_text(entry: DiffEntry) -> Optional[str]:
    symbol = _STATUS_SYMBOL.get(entry.status, "?")
    if entry.status == DiffStatus.ADDED:
        return f"{symbol} {entry.key}={entry.new_value}"
    if entry.status == DiffStatus.REMOVED:
        return f"{symbol} {entry.key}={entry.old_value}"
    if entry.status == DiffStatus.CHANGED:
        return f"{symbol} {entry.key}: {entry.old_value!r} -> {entry.new_value!r}"
    return None  # unchanged entries are skipped by default


def format_text(result: DiffResult, show_summary: bool = False) -> str:
    """Render diff as human-readable text.

    Args:
        result: The diff result to format.
        show_summary: If True, append a summary block at the end.
    """
    lines = []
    for entry in result.entries:
        line = _format_entry_text(entry)
        if line is not None:
            lines.append(line)

    if show_summary:
        if lines:
            lines.append("")
        lines.append(format_summary_text(summarize(result)))

    return "\n".join(lines)


def format_json(result: DiffResult, show_summary: bool = False) -> str:
    """Render diff as a JSON string.

    Args:
        result: The diff result to format.
        show_summary: If True, include a 'summary' key in the output.
    """
    entries = [
        {
            "key": e.key,
            "status": e.status.value,
            "old_value": e.old_value,
            "new_value": e.new_value,
        }
        for e in result.entries
        if e.status != DiffStatus.UNCHANGED
    ]
    payload = {"diff": entries}
    if show_summary:
        payload["summary"] = summarize(result).as_dict()
    return json.dumps(payload, indent=2)
