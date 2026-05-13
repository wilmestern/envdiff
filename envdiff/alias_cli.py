"""CLI entry point for the env-alias command."""

import argparse
import json
import sys
from typing import List

from envdiff.env_alias import apply_aliases, find_unresolved
from envdiff.loader import load_from_file


def build_alias_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-alias",
        description="Apply key aliases to an environment file.",
    )
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--alias",
        metavar="CANONICAL=ALIAS",
        action="append",
        default=[],
        dest="aliases",
        help="Alias mapping, e.g. DATABASE_URL=DB_URL (repeatable)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing canonical keys",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return p


def _parse_aliases(raw: List[str]) -> dict:
    result = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid alias format (expected CANONICAL=ALIAS): {item!r}")
        canonical, alias = item.split("=", 1)
        result[canonical.strip()] = alias.strip()
    return result


def run_alias(argv: List[str] = None) -> int:
    parser = build_alias_parser()
    args = parser.parse_args(argv)

    try:
        aliases = _parse_aliases(args.aliases)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    source = load_from_file(args.file)
    result = apply_aliases(source.data, aliases, overwrite=args.overwrite)
    unresolved = find_unresolved(source.data, aliases)

    if args.format == "json":
        print(json.dumps({**result.as_dict(), "unresolved": sorted(unresolved)}, indent=2))
    else:
        if result.applied:
            print(f"Applied aliases ({len(result.applied)}):")
            for k in sorted(result.applied):
                print(f"  {k} <- {aliases[k]}")
        if result.skipped:
            print(f"Skipped ({len(result.skipped)}): {', '.join(sorted(result.skipped))}")
        if unresolved:
            print(f"Unresolved ({len(unresolved)}): {', '.join(sorted(unresolved))}")
        if not result.has_changes():
            print("No aliases applied.")

    return 0


def main():
    sys.exit(run_alias())
