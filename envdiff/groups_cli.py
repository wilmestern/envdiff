"""CLI entry point for the env-groups subcommand."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.env_grouper import format_groups_text, group_by_prefix
from envdiff.loader import load_from_file


def build_groups_parser(prog: Optional[str] = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog or "envdiff-groups",
        description="Group environment variables by prefix namespace.",
    )
    parser.add_argument("file", help="Path to .env file to analyse")
    parser.add_argument(
        "--separator",
        default="_",
        help="Prefix separator character (default: '_')",
    )
    parser.add_argument(
        "--min-group-size",
        type=int,
        default=1,
        dest="min_group_size",
        help="Minimum keys required to form a named group (default: 1)",
    )
    parser.add_argument(
        "--ungrouped-label",
        default="OTHER",
        dest="ungrouped_label",
        help="Label for keys that don't belong to any group (default: OTHER)",
    )
    parser.add_argument(
        "--show-values",
        action="store_true",
        dest="show_values",
        help="Display values alongside keys",
    )
    parser.add_argument(
        "--redact",
        action="store_true",
        help="Redact sensitive values when --show-values is active",
    )
    return parser


def run_groups(argv: Optional[List[str]] = None) -> int:
    parser = build_groups_parser()
    args = parser.parse_args(argv)

    try:
        source = load_from_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    env = source.data
    groups = group_by_prefix(
        env,
        separator=args.separator,
        min_group_size=args.min_group_size,
        ungrouped_label=args.ungrouped_label,
    )

    display_env = env if args.show_values else None
    text = format_groups_text(groups, env=display_env, redact=args.redact)
    print(text)
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_groups())
