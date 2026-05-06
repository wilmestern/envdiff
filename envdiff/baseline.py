"""Baseline management: capture and compare against a known-good environment state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.redactor import redact_env


@dataclass
class Baseline:
    """A named, timestamped snapshot of environment variables used as a reference point."""

    name: str
    data: Dict[str, str]
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: Optional[str] = None

    def __repr__(self) -> str:
        return f"Baseline(name={self.name!r}, keys={len(self.data)}, captured_at={self.captured_at!r})"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "captured_at": self.captured_at,
            "description": self.description,
            "data": self.data,
        }

    def redacted(self) -> "Baseline":
        """Return a copy of this baseline with sensitive values redacted."""
        return Baseline(
            name=self.name,
            data=redact_env(self.data),
            captured_at=self.captured_at,
            description=self.description,
        )


def save_baseline(baseline: Baseline, path: Path) -> None:
    """Persist a baseline to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(baseline.as_dict(), indent=2), encoding="utf-8")


def load_baseline(path: Path) -> Baseline:
    """Load a baseline from a JSON file."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return Baseline(
        name=raw["name"],
        data=raw["data"],
        captured_at=raw["captured_at"],
        description=raw.get("description"),
    )


def compare_to_baseline(current: Dict[str, str], baseline: Baseline) -> DiffResult:
    """Diff *current* env against *baseline*, returning a DiffResult."""
    return diff_envs(baseline.data, current)
