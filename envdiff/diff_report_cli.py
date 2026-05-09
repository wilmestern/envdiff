"""CLI entry point for generating structured diff reports."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.differ import diff_envs
from envdiff.env_differ_report import build_diff_report, format_diff_report_text
from envdiff.loader import load_from_file


def build_diff_report_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-report",
        description="Generate a structured diff report between two .env files.",
    )
    parser.add_argument("left", help="Path to the left (base) .env file")
    parser.add_argument("right", help="Path to the right (target) .env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional title for the report",
    )
    parser.add_argument(
        "--redact",
        action="store_true",
        default=False,
        help="Redact sensitive values in output",
    )
    return parser


def run_diff_report(args: argparse.Namespace, out=sys.stdout) -> int:
    try:
        left_src = load_from_file(args.left)
        right_src = load_from_file(args.right)
    except (FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = diff_envs(left_src, right_src, include_unchanged=False)
    report = build_diff_report(
        result=result,
        left_env=dict(left_src),
        right_env=dict(right_src),
        left_name=left_src.name,
        right_name=right_src.name,
        title=args.title,
    )

    if args.format == "json":
        print(json.dumps(report.as_dict(), indent=2), file=out)
    else:
        print(format_diff_report_text(report), file=out)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_diff_report_parser()
    args = parser.parse_args()
    sys.exit(run_diff_report(args))
