"""Utilities for detecting stale/rotated environment variable values."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from envdiff.baseline import Baseline
from envdiff.redactor import is_sensitive, redact_value


@dataclass
class RotationEntry:
    key: str
    old_value: str
    new_value: str
    sensitive: bool = False

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "old_value": redact_value(self.key, self.old_value) if self.sensitive else self.old_value,
            "new_value": redact_value(self.key, self.new_value) if self.sensitive else self.new_value,
            "sensitive": self.sensitive,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"RotationEntry(key={self.key!r}, sensitive={self.sensitive})"


@dataclass
class RotationReport:
    name: str
    rotated: List[RotationEntry] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def has_rotations(self) -> bool:
        return bool(self.rotated)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "generated_at": self.generated_at,
            "rotated": [e.as_dict() for e in self.rotated],
            "unchanged": sorted(self.unchanged),
            "added": sorted(self.added),
            "removed": sorted(self.removed),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RotationReport(name={self.name!r}, rotated={len(self.rotated)}, "
            f"added={len(self.added)}, removed={len(self.removed)})"
        )


def detect_rotations(
    baseline: Baseline,
    current: Dict[str, str],
    sensitive_only: bool = False,
) -> RotationReport:
    """Compare *current* env against *baseline* and report changed values."""
    report = RotationReport(name=baseline.name)
    old_data: Dict[str, str] = baseline.data

    all_keys = set(old_data) | set(current)
    for key in sorted(all_keys):
        in_old = key in old_data
        in_new = key in current
        if in_old and not in_new:
            report.removed.append(key)
        elif in_new and not in_old:
            report.added.append(key)
        else:
            sensitive = is_sensitive(key)
            if sensitive_only and not sensitive:
                continue
            if old_data[key] != current[key]:
                report.rotated.append(
                    RotationEntry(
                        key=key,
                        old_value=old_data[key],
                        new_value=current[key],
                        sensitive=sensitive,
                    )
                )
            else:
                report.unchanged.append(key)
    return report
