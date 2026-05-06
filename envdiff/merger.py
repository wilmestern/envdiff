"""Merge two env sets with configurable conflict resolution strategies."""

from enum import Enum
from typing import Dict, Optional

from envdiff.loader import EnvSource


class MergeStrategy(str, Enum):
    PREFER_LEFT = "prefer_left"
    PREFER_RIGHT = "prefer_right"
    RAISE_ON_CONFLICT = "raise_on_conflict"
    KEEP_BOTH = "keep_both"  # suffix keys with source name


class MergeConflict(Exception):
    """Raised when RAISE_ON_CONFLICT strategy encounters a differing key."""

    def __init__(self, key: str, left_val: str, right_val: str) -> None:
        self.key = key
        self.left_val = left_val
        self.right_val = right_val
        super().__init__(
            f"Conflict on key '{key}': '{left_val}' vs '{right_val}'"
        )


def merge_envs(
    left: EnvSource,
    right: EnvSource,
    strategy: MergeStrategy = MergeStrategy.PREFER_LEFT,
) -> Dict[str, str]:
    """Merge two EnvSource objects into a single dict.

    Args:
        left: The primary / base env source.
        right: The secondary env source to merge in.
        strategy: How to handle keys present in both sources.

    Returns:
        A merged dictionary of environment variables.

    Raises:
        MergeConflict: When strategy is RAISE_ON_CONFLICT and a key differs.
    """
    merged: Dict[str, str] = {}
    left_data: Dict[str, str] = dict(left)
    right_data: Dict[str, str] = dict(right)

    all_keys = set(left_data) | set(right_data)

    for key in sorted(all_keys):
        in_left = key in left_data
        in_right = key in right_data

        if in_left and not in_right:
            merged[key] = left_data[key]
        elif in_right and not in_left:
            merged[key] = right_data[key]
        else:
            # Key exists in both
            lv, rv = left_data[key], right_data[key]
            if lv == rv:
                merged[key] = lv
            elif strategy == MergeStrategy.PREFER_LEFT:
                merged[key] = lv
            elif strategy == MergeStrategy.PREFER_RIGHT:
                merged[key] = rv
            elif strategy == MergeStrategy.RAISE_ON_CONFLICT:
                raise MergeConflict(key, lv, rv)
            elif strategy == MergeStrategy.KEEP_BOTH:
                merged[f"{key}__{left.name.upper()}"] = lv
                merged[f"{key}__{right.name.upper()}"] = rv

    return merged


def list_conflicts(left: EnvSource, right: EnvSource) -> Dict[str, tuple]:
    """Return all keys that have differing values between two EnvSource objects.

    Args:
        left: The primary / base env source.
        right: The secondary env source to compare against.

    Returns:
        A dict mapping each conflicting key to a ``(left_value, right_value)``
        tuple.  Keys that are identical in both sources are excluded.
    """
    left_data: Dict[str, str] = dict(left)
    right_data: Dict[str, str] = dict(right)
    shared_keys = set(left_data) & set(right_data)
    return {
        key: (left_data[key], right_data[key])
        for key in sorted(shared_keys)
        if left_data[key] != right_data[key]
    }
