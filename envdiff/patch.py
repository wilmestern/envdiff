"""Generate a minimal dotenv patch to reconcile one env into another."""

from dataclasses import dataclass, field
from typing import Dict, List

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class EnvPatch:
    """Represents the operations needed to transform source into target."""

    additions: Dict[str, str] = field(default_factory=dict)
    updates: Dict[str, str] = field(default_factory=dict)
    deletions: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.additions or self.updates or self.deletions)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"EnvPatch(additions={len(self.additions)}, "
            f"updates={len(self.updates)}, "
            f"deletions={len(self.deletions)})"
        )


def build_patch(diff: DiffResult) -> EnvPatch:
    """Build an EnvPatch from a DiffResult.

    The patch represents changes needed to make *left* look like *right*
    (i.e. apply right's additions/removals/changes onto left).

    Args:
        diff: A DiffResult produced by differ.diff_envs.

    Returns:
        An EnvPatch describing additions, updates and deletions.
    """
    patch = EnvPatch()

    for entry in diff.entries:
        if entry.status == DiffStatus.ADDED:
            # Present in right but not left → add to left
            patch.additions[entry.key] = entry.right_value or ""
        elif entry.status == DiffStatus.REMOVED:
            # Present in left but not right → delete from left
            patch.deletions.append(entry.key)
        elif entry.status == DiffStatus.CHANGED:
            # Value differs → update left to match right
            patch.updates[entry.key] = entry.right_value or ""

    patch.deletions.sort()
    return patch


def render_patch_dotenv(patch: EnvPatch) -> str:
    """Render an EnvPatch as a dotenv-compatible string.

    Deletions are rendered as commented-out UNSET directives.

    Args:
        patch: The EnvPatch to render.

    Returns:
        A string suitable for writing to a .env.patch file.
    """
    lines: List[str] = []

    if patch.additions:
        lines.append("# --- Additions ---")
        for k, v in sorted(patch.additions.items()):
            lines.append(f"{k}={v}")

    if patch.updates:
        lines.append("# --- Updates ---")
        for k, v in sorted(patch.updates.items()):
            lines.append(f"{k}={v}")

    if patch.deletions:
        lines.append("# --- Deletions ---")
        for k in patch.deletions:
            lines.append(f"# UNSET {k}")

    return "\n".join(lines)
