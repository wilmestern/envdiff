"""CLI entry-point for env-rotation detection."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.baseline_store import BaselineStore
from envdiff.env_rotator import detect_rotations, RotationReport
from envdiff.loader import load_from_file


def build_rotation_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-rotation",
        description="Detect rotated/changed env vars compared to a saved baseline.",
    )
    p.add_argument("file", help="Current .env file to compare against the baseline")
    p.add_argument("--baseline", required=True, help="Baseline name stored via baseline-store")
    p.add_argument(
        "--store-dir",
        default=".envdiff_baselines",
        help="Directory where baselines are persisted (default: .envdiff_baselines)",
    )
    p.add_argument(
        "--sensitive-only",
        action="store_true",
        help="Only report rotations for sensitive keys",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def _format_report_text(report: RotationReport) -> str:
    lines = [f"Rotation report for baseline: {report.name}"]
    if report.rotated:
        lines.append(f"\nRotated ({len(report.rotated)}):")
        for entry in report.rotated:
            tag = " [sensitive]" if entry.sensitive else ""
            lines.append(f"  {entry.key}{tag}")
    if report.added:
        lines.append(f"\nAdded ({len(report.added)}):")
        for k in report.added:
            lines.append(f"  + {k}")
    if report.removed:
        lines.append(f"\nRemoved ({len(report.removed)}):")
        for k in report.removed:
            lines.append(f"  - {k}")
    if not report.rotated and not report.added and not report.removed:
        lines.append("No rotations detected.")
    return "\n".join(lines)


def run_rotation(argv: list[str] | None = None) -> int:
    parser = build_rotation_parser()
    args = parser.parse_args(argv)

    store = BaselineStore(args.store_dir)
    if not store.exists(args.baseline):
        print(f"Error: baseline '{args.baseline}' not found in {args.store_dir}", file=sys.stderr)
        return 1

    baseline = store.load(args.baseline)
    source = load_from_file(args.file)
    report = detect_rotations(baseline, dict(source), sensitive_only=args.sensitive_only)

    if args.format == "json":
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(_format_report_text(report))

    return 1 if report.has_rotations else 0


def main() -> None:  # pragma: no cover
    sys.exit(run_rotation())
