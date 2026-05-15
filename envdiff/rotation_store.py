"""Persist and retrieve rotation reports."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List

from envdiff.env_rotator import RotationReport, RotationEntry


class RotationStore:
    """File-backed store for serialised :class:`RotationReport` objects."""

    def __init__(self, directory: str = ".envdiff_rotations") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        safe = name.replace(os.sep, "_")
        return self.directory / f"{safe}.json"

    def save(self, report: RotationReport) -> None:
        """Serialise *report* to disk."""
        data = report.as_dict()
        # Store raw (un-redacted) rotated entries separately for round-trip.
        data["_rotated_raw"] = [
            {"key": e.key, "old_value": e.old_value, "new_value": e.new_value, "sensitive": e.sensitive}
            for e in report.rotated
        ]
        self._path_for(report.name).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self, name: str) -> RotationReport:
        """Deserialise a previously saved report."""
        raw = json.loads(self._path_for(name).read_text(encoding="utf-8"))
        rotated: List[RotationEntry] = [
            RotationEntry(
                key=e["key"],
                old_value=e["old_value"],
                new_value=e["new_value"],
                sensitive=e.get("sensitive", False),
            )
            for e in raw.get("_rotated_raw", [])
        ]
        return RotationReport(
            name=raw["name"],
            rotated=rotated,
            unchanged=raw.get("unchanged", []),
            added=raw.get("added", []),
            removed=raw.get("removed", []),
            generated_at=raw.get("generated_at", ""),
        )

    def exists(self, name: str) -> bool:
        return self._path_for(name).exists()

    def list_names(self) -> List[str]:
        return sorted(
            p.stem for p in self.directory.glob("*.json")
        )

    def delete(self, name: str) -> None:
        path = self._path_for(name)
        if path.exists():
            path.unlink()
