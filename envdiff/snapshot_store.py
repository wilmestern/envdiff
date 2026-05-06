"""Simple filesystem-backed store for multiple named snapshots."""

from __future__ import annotations

import os
from typing import Iterator, List

from envdiff.snapshot import EnvSnapshot, load_snapshot, save_snapshot

_SUFFIX = ".snapshot.json"


class SnapshotStore:
    """Manages a directory of snapshot files."""

    def __init__(self, directory: str) -> None:
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path_for(self, name: str) -> str:
        safe = name.replace(os.sep, "_")
        return os.path.join(self.directory, f"{safe}{_SUFFIX}")

    def save(self, snapshot: EnvSnapshot) -> str:
        """Persist *snapshot* and return the file path."""
        path = self._path_for(snapshot.name)
        save_snapshot(snapshot, path)
        return path

    def load(self, name: str) -> EnvSnapshot:
        """Load the snapshot identified by *name*."""
        return load_snapshot(self._path_for(name))

    def exists(self, name: str) -> bool:
        return os.path.isfile(self._path_for(name))

    def list_names(self) -> List[str]:
        """Return sorted list of stored snapshot names."""
        names = []
        for fname in os.listdir(self.directory):
            if fname.endswith(_SUFFIX):
                names.append(fname[: -len(_SUFFIX)])
        return sorted(names)

    def __iter__(self) -> Iterator[EnvSnapshot]:
        for name in self.list_names():
            yield self.load(name)

    def __len__(self) -> int:
        return len(self.list_names())

    def __repr__(self) -> str:  # pragma: no cover
        return f"SnapshotStore(directory={self.directory!r}, count={len(self)})"
