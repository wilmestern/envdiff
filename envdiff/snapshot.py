"""Snapshot support: capture and persist environment state for later comparison."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional


@dataclass
class EnvSnapshot:
    """A named, timestamped capture of an environment variable mapping."""

    name: str
    data: Dict[str, str]
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    description: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvSnapshot(name={self.name!r}, keys={len(self.data)}, "
            f"captured_at={self.captured_at!r})"
        )

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "captured_at": self.captured_at,
            "description": self.description,
            "data": self.data,
        }


def save_snapshot(snapshot: EnvSnapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.as_dict(), fh, indent=2)
        fh.write("\n")


def load_snapshot(path: str) -> EnvSnapshot:
    """Load a snapshot from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return EnvSnapshot(
        name=raw["name"],
        data=raw["data"],
        captured_at=raw.get("captured_at", ""),
        description=raw.get("description"),
    )


def snapshot_from_mapping(
    name: str,
    mapping: Dict[str, str],
    description: Optional[str] = None,
) -> EnvSnapshot:
    """Create a snapshot from an arbitrary string mapping."""
    return EnvSnapshot(name=name, data=dict(mapping), description=description)
