"""Diff engine for comparing two environment variable sets."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from envdiff.redactor import redact_env


class DiffStatus(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


@dataclass
class DiffEntry:
    key: str
    status: DiffStatus
    left_value: Optional[str] = None
    right_value: Optional[str] = None

    def __repr__(self) -> str:
        return f"DiffEntry(key={self.key!r}, status={self.status.value})"


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.ADDED]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.REMOVED]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.CHANGED]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == DiffStatus.UNCHANGED]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> Dict[str, int]:
        """Return a count of entries grouped by status.

        Returns:
            A dict mapping each status value to the number of entries with that status.
        """
        return {
            DiffStatus.ADDED.value: len(self.added),
            DiffStatus.REMOVED.value: len(self.removed),
            DiffStatus.CHANGED.value: len(self.changed),
            DiffStatus.UNCHANGED.value: len(self.unchanged),
        }


def diff_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    redact: bool = True,
    include_unchanged: bool = False,
) -> DiffResult:
    """Compare two environment variable dictionaries and return a DiffResult.

    Args:
        left: The base environment (e.g. staging).
        right: The target environment (e.g. production).
        redact: Whether to redact sensitive values before comparison.
        include_unchanged: Whether to include unchanged keys in the result.

    Returns:
        A DiffResult containing categorised DiffEntry objects.
    """
    if redact:
        left = redact_env(left)
        right = redact_env(right)

    all_keys = sorted(set(left) | set(right))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_left = key in left
        in_right = key in right

        if in_left and not in_right:
            entries.append(DiffEntry(key, DiffStatus.REMOVED, left_value=left[key]))
        elif in_right and not in_left:
            entries.append(DiffEntry(key, DiffStatus.ADDED, right_value=right[key]))
        elif left[key] != right[key]:
            entries.append(
                DiffEntry(key, DiffStatus.CHANGED, left_value=left[key], right_value=right[key])
            )
        elif include_unchanged:
            entries.append(
                DiffEntry(key, DiffStatus.UNCHANGED, left_value=left[key], right_value=right[key])
            )

    return DiffResult(entries=entries)
