"""Compare two EnvSnapshot objects and return a DiffResult."""

from __future__ import annotations

from typing import Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.loader import EnvSource
from envdiff.snapshot import EnvSnapshot


def diff_snapshots(
    before: EnvSnapshot,
    after: EnvSnapshot,
    *,
    include_unchanged: bool = False,
    redact: bool = True,
) -> DiffResult:
    """Diff two snapshots and return a :class:`DiffResult`.

    Parameters
    ----------
    before:
        The baseline snapshot (treated as the *left* / staging side).
    after:
        The newer snapshot (treated as the *right* / production side).
    include_unchanged:
        When *True* unchanged keys are included in the result.
    redact:
        Passed through to :func:`diff_envs` to control value redaction.
    """
    left = EnvSource(name=before.name, data=before.data)
    right = EnvSource(name=after.name, data=after.data)
    return diff_envs(left, right, include_unchanged=include_unchanged, redact=redact)


def snapshot_summary_line(before: EnvSnapshot, after: EnvSnapshot) -> str:
    """Return a one-line human-readable summary of snapshot differences."""
    result = diff_snapshots(before, after, include_unchanged=False)
    added = sum(1 for e in result.entries if e.status.name == "ADDED")
    removed = sum(1 for e in result.entries if e.status.name == "REMOVED")
    changed = sum(1 for e in result.entries if e.status.name == "CHANGED")
    return (
        f"{before.name!r} → {after.name!r}: "
        f"+{added} added, -{removed} removed, ~{changed} changed"
    )
