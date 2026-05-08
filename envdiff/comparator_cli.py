"""CLI entry point for side-by-side env comparison."""

import argparse
import json
import sys

from envdiff.loader import load_from_file, load_from_string
from envdiff.env_comparator import compare_envs, format_comparison_text


def build_comparator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-compare",
        description="Side-by-side comparison of two .env files.",
    )
    parser.add_argument("left", help="Path to the left/base .env file")
    parser.add_argument("right", help="Path to the right/target .env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable redaction of sensitive values",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="include_unchanged",
        help="Include unchanged keys in output",
    )
    return parser


def run_comparator(args: argparse.Namespace, out=sys.stdout) -> int:
    try:
        left_src = load_from_file(args.left)
        right_src = load_from_file(args.right)
    except (FileNotFoundError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = compare_envs(
        left=left_src.data,
        right=right_src.data,
        left_name=left_src.name,
        right_name=right_src.name,
        redact=not args.no_redact,
        include_unchanged=args.include_unchanged,
    )

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2), file=out)
    else:
        print(format_comparison_text(result), file=out)

    return 0 if not result.has_differences else 1


def main() -> None:  # pragma: no cover
    parser = build_comparator_parser()
    args = parser.parse_args()
    sys.exit(run_comparator(args))
