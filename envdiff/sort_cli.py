"""CLI entry point for the env-sort subcommand."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envdiff.loader import load_from_file
from envdiff.env_sorter import sort_env, sort_by_prefix, format_sorted_text


def build_sort_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:
    """Build the argument parser for the sort command."""
    kwargs = dict(
        description="Sort environment variable keys in one or more .env files."
    )
    if parent is not None:
        parser = parent.add_parser("sort", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("files", nargs="+", metavar="FILE", help=".env files to sort")
    parser.add_argument(
        "--prefix",
        dest="prefixes",
        metavar="PREFIX",
        action="append",
        default=[],
        help="Priority prefix (repeatable); matching keys appear first",
    )
    parser.add_argument(
        "--reverse", action="store_true", default=False, help="Reverse sort order"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def _sort_file(path: str, prefixes: List[str], reverse: bool) -> dict:
    source = load_from_file(path)
    if prefixes:
        sorted_data = sort_by_prefix(source.data, prefixes, reverse=reverse)
    else:
        sorted_data = sort_env(source.data, reverse=reverse)
    return {"name": source.name, "data": sorted_data}


def run_sort(args: argparse.Namespace) -> int:
    results = [_sort_file(f, args.prefixes, args.reverse) for f in args.files]

    if args.format == "json":
        payload = [{"file": r["name"], "env": r["data"]} for r in results]
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            block = format_sorted_text(r["data"], title=r["name"])
            print(block)
            print()
    return 0


def main(argv=None) -> None:
    parser = build_sort_parser()
    args = parser.parse_args(argv)
    sys.exit(run_sort(args))


if __name__ == "__main__":
    main()
