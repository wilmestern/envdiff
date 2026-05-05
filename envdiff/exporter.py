"""Export diff results to various file formats (JSON, text, dotenv patch)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

from envdiff.differ import DiffResult, DiffStatus
from envdiff.formatter import format_text, format_json


def export_text(result: DiffResult, path: Union[str, Path], *, show_unchanged: bool = False) -> int:
    """Write a human-readable text diff to *path*.

    Returns the number of bytes written.
    """
    content = format_text(result, show_unchanged=show_unchanged)
    return _write(path, content)


def export_json(result: DiffResult, path: Union[str, Path], *, show_unchanged: bool = False) -> int:
    """Write a JSON diff to *path*.

    Returns the number of bytes written.
    """
    content = format_json(result, show_unchanged=show_unchanged)
    return _write(path, content)


def export_dotenv_patch(
    result: DiffResult,
    path: Union[str, Path],
    *,
    target: str = "right",
) -> int:
    """Write a dotenv-formatted patch file reflecting the *target* side.

    Only ADDED and CHANGED keys (relative to the left/source side) are
    included.  REMOVED keys are emitted as commented-out entries so the
    file remains valid dotenv syntax.

    Returns the number of bytes written.
    """
    lines: list[str] = [
        "# envdiff patch — apply to source environment to reach target\n"
    ]

    for entry in result.entries:
        if entry.status == DiffStatus.ADDED:
            lines.append(f"{entry.key}={_quote(entry.right_value)}\n")
        elif entry.status == DiffStatus.CHANGED:
            lines.append(f"{entry.key}={_quote(entry.right_value)}\n")
        elif entry.status == DiffStatus.REMOVED:
            lines.append(f"# REMOVED: {entry.key}\n")
        # UNCHANGED entries are intentionally skipped

    content = "".join(lines)
    return _write(path, content)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Union[str, Path], content: str) -> int:
    """Write *content* to *path*, creating parent directories as needed."""
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode()
    dest.write_bytes(data)
    return len(data)


def _quote(value: str | None) -> str:
    """Return a dotenv-safe representation of *value*."""
    if value is None:
        return ""
    if any(c in value for c in (" ", "\t", '"', "'", "#", "=")):
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    return value
