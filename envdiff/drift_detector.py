"""Drift detection: compare a live env against a saved baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.baseline import Baseline
from envdiff.differ import DiffEntry, DiffResult, DiffStatus, diff_envs


@dataclass
class DriftReport:
    """Result of comparing an environment against a baseline."""

    baseline_name: str
    added: List[DiffEntry] = field(default_factory=list)
    removed: List[DiffEntry] = field(default_factory=list)
    changed: List[DiffEntry] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        """Return True if any differences were detected."""
        return bool(self.added or self.removed or self.changed)

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.changed)

    def as_dict(self) -> Dict:
        return {
            "baseline_name": self.baseline_name,
            "has_drift": self.has_drift,
            "total_changes": self.total_changes,
            "added": [e.key for e in self.added],
            "removed": [e.key for e in self.removed],
            "changed": [e.key for e in self.changed],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DriftReport(baseline={self.baseline_name!r}, "
            f"added={len(self.added)}, removed={len(self.removed)}, "
            f"changed={len(self.changed)})"
        )


def detect_drift(
    current: Dict[str, str],
    baseline: Baseline,
    redact: bool = False,
) -> DriftReport:
    """Compare *current* env data against *baseline* and return a DriftReport.

    Parameters
    ----------
    current:
        Mapping of key -> value representing the live environment.
    baseline:
        A :class:`~envdiff.baseline.Baseline` to compare against.
    redact:
        When *True*, use the redacted view of the baseline for comparison.
    """
    baseline_data: Dict[str, str] = (
        baseline.redacted() if redact else dict(baseline.data)
    )

    result: DiffResult = diff_envs(
        baseline_data,
        current,
        include_unchanged=False,
    )

    report = DriftReport(baseline_name=baseline.name)
    for entry in result.entries:
        if entry.status == DiffStatus.ADDED:
            report.added.append(entry)
        elif entry.status == DiffStatus.REMOVED:
            report.removed.append(entry)
        elif entry.status == DiffStatus.CHANGED:
            report.changed.append(entry)

    return report
