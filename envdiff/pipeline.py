"""High-level pipeline combining load → diff → merge → patch in one call."""

from dataclasses import dataclass
from typing import Dict, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.loader import EnvSource, load_from_string
from envdiff.merger import MergeStrategy, merge_envs
from envdiff.patch import EnvPatch, build_patch
from envdiff.reporter import DiffSummary, summarize


@dataclass
class PipelineResult:
    """Aggregated output of a full envdiff pipeline run."""

    left: EnvSource
    right: EnvSource
    diff: DiffResult
    summary: DiffSummary
    merged: Dict[str, str]
    patch: EnvPatch


def run_pipeline(
    left_source: EnvSource,
    right_source: EnvSource,
    strategy: MergeStrategy = MergeStrategy.PREFER_LEFT,
    redact: bool = False,
) -> PipelineResult:
    """Run the full envdiff pipeline on two EnvSource objects.

    Steps:
      1. Diff the two sources.
      2. Summarize the diff.
      3. Merge the two sources using the given strategy.
      4. Build a patch to reconcile left → right.

    Args:
        left_source: The base / left environment.
        right_source: The target / right environment.
        strategy: Merge conflict resolution strategy.
        redact: If True, redact sensitive values before diffing.

    Returns:
        A PipelineResult containing all intermediate and final outputs.
    """
    from envdiff.redactor import redact_env  # local to avoid circular import

    left = left_source
    right = right_source

    if redact:
        left = EnvSource(name=left.name, data=redact_env(dict(left)))
        right = EnvSource(name=right.name, data=redact_env(dict(right)))

    diff = diff_envs(left, right)
    summary = summarize(diff)
    merged = merge_envs(left, right, strategy=strategy)
    patch = build_patch(diff)

    return PipelineResult(
        left=left,
        right=right,
        diff=diff,
        summary=summary,
        merged=merged,
        patch=patch,
    )


def run_pipeline_from_strings(
    left_text: str,
    right_text: str,
    left_name: str = "left",
    right_name: str = "right",
    strategy: MergeStrategy = MergeStrategy.PREFER_LEFT,
    redact: bool = False,
) -> PipelineResult:
    """Convenience wrapper that parses raw env strings before running."""
    left = load_from_string(left_text, name=left_name)
    right = load_from_string(right_text, name=right_name)
    return run_pipeline(left, right, strategy=strategy, redact=redact)
