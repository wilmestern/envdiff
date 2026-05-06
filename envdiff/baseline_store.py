"""File-system backed store for multiple named baselines."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envdiff.baseline import Baseline, load_baseline, save_baseline


class BaselineStore:
    """Manages a directory of baseline JSON files, keyed by name."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        safe = name.replace("/", "_").replace("\\", "_")
        return self.directory / f"{safe}.baseline.json"

    def save(self, baseline: Baseline) -> None:
        """Persist *baseline* under its name."""
        save_baseline(baseline, self._path_for(baseline.name))

    def load(self, name: str) -> Baseline:
        """Load and return the baseline stored under *name*."""
        path = self._path_for(name)
        if not path.exists():
            raise FileNotFoundError(f"No baseline named {name!r} in {self.directory}")
        return load_baseline(path)

    def exists(self, name: str) -> bool:
        return self._path_for(name).exists()

    def delete(self, name: str) -> bool:
        """Remove the baseline. Returns True if it existed."""
        path = self._path_for(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_names(self) -> List[str]:
        """Return sorted list of stored baseline names."""
        names = []
        for p in self.directory.glob("*.baseline.json"):
            names.append(p.name.replace(".baseline.json", ""))
        return sorted(names)

    def __repr__(self) -> str:
        return f"BaselineStore(directory={str(self.directory)!r}, count={len(self.list_names())})"
