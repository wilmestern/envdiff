"""Rename environment variable keys across an env mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameResult:
    """Outcome of a bulk rename operation."""

    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)        # keys not found
    conflicts: List[str] = field(default_factory=list)      # new_key already existed

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    @property
    def has_skipped(self) -> bool:
        return bool(self.skipped)

    def as_dict(self) -> dict:
        return {
            "renamed": self.renamed,
            "skipped": self.skipped,
            "conflicts": self.conflicts,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RenameResult(renamed={len(self.renamed)}, "
            f"skipped={len(self.skipped)}, conflicts={len(self.conflicts)})"
        )


def rename_keys(
    env: Dict[str, str],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> tuple[Dict[str, str], RenameResult]:
    """Return a new env dict with keys renamed according to *mapping*.

    Parameters
    ----------
    env:
        Source environment mapping.
    mapping:
        Dict of {old_key: new_key} rename instructions.
    overwrite:
        When *True*, allow renaming even if *new_key* already exists in *env*
        (the existing value is replaced).  Defaults to *False*.

    Returns
    -------
    (new_env, result)
        *new_env* is the updated mapping; *result* contains bookkeeping info.
    """
    result = RenameResult()
    output = dict(env)

    for old_key, new_key in mapping.items():
        if old_key not in output:
            result.skipped.append(old_key)
            continue

        if new_key in output and new_key != old_key and not overwrite:
            result.conflicts.append(new_key)
            continue

        value = output.pop(old_key)
        output[new_key] = value
        result.renamed[old_key] = new_key

    return output, result


def format_rename_text(result: RenameResult) -> str:
    """Return a human-readable summary of a RenameResult."""
    lines: List[str] = []
    for old, new in sorted(result.renamed.items()):
        lines.append(f"  RENAMED  {old} -> {new}")
    for key in sorted(result.skipped):
        lines.append(f"  SKIPPED  {key} (not found)")
    for key in sorted(result.conflicts):
        lines.append(f"  CONFLICT {key} (target key already exists)")
    if not lines:
        return "No renames performed."
    return "\n".join(lines)
