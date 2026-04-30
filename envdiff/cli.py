"""Command-line interface for envdiff."""

import argparse
import sys
from typing import List, Optional

from envdiff.loader import load_from_file
from envdiff.differ import diff_envs
from envdiff.formatter import format_text, format_json
from envdiff.redactor import redact_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare environment variable sets across configs.",
    )
    parser.add_argument("file_a", help="First env file (e.g. staging.env)")
    parser.add_argument("file_b", help="Second env file (e.g. production.env)")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--show-unchanged",
        action="store_true",
        default=False,
        help="Include unchanged keys in output",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        default=False,
        help="Disable redaction of sensitive values",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        source_a = load_from_file(args.file_a)
        source_b = load_from_file(args.file_b)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    env_a = source_a.data
    env_b = source_b.data

    if not args.no_redact:
        env_a = redact_env(env_a)
        env_b = redact_env(env_b)

    result = diff_envs(env_a, env_b)

    if args.format == "json":
        output = format_json(result, include_unchanged=args.show_unchanged)
    else:
        output = format_text(
            result,
            label_a=source_a.name,
            label_b=source_b.name,
            include_unchanged=args.show_unchanged,
        )

    print(output)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
