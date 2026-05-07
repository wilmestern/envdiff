"""CLI entry-point for scoring environment files."""

import argparse
import json
import sys
from typing import List, Optional

from envdiff.loader import load_from_file
from envdiff.env_scorer import score_env, format_score_text


def build_score_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Score environment files for quality and completeness.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to score.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--fail-below",
        type=float,
        default=None,
        metavar="THRESHOLD",
        help="Exit with code 1 if any file scores below THRESHOLD.",
    )
    return parser


def run_score(argv: Optional[List[str]] = None) -> int:
    parser = build_score_parser()
    args = parser.parse_args(argv)

    scores = []
    for filepath in args.files:
        try:
            source = load_from_file(filepath)
        except FileNotFoundError:
            print(f"error: file not found: {filepath}", file=sys.stderr)
            return 2
        scores.append(score_env(source.name, source.data))

    if args.format == "json":
        print(json.dumps([s.as_dict() for s in scores], indent=2))
    else:
        for s in scores:
            print(format_score_text(s))
            print()

    if args.fail_below is not None:
        if any(s.score < args.fail_below for s in scores):
            return 1

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_score())
