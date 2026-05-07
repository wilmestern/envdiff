"""CLI entry-point for the env-rename sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.env_renamer import format_rename_text, rename_keys
from envdiff.loader import load_from_file


def build_rename_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    description = "Rename environment variable keys in a .env file."
    if parent is not None:
        parser = parent.add_parser("rename", description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-rename", description=description)

    parser.add_argument("file", help="Path to the .env file to rename keys in.")
    parser.add_argument(
        "--rename",
        metavar="OLD=NEW",
        action="append",
        dest="renames",
        required=True,
        help="Rename rule in OLD=NEW format.  May be repeated.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow renaming even if the target key already exists.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _parse_renames(raw: List[str]) -> dict:
    mapping: dict = {}
    for item in raw:
        if "=" not in item:
            print(f"error: invalid rename rule {item!r} (expected OLD=NEW)", file=sys.stderr)
            sys.exit(1)
        old, _, new = item.partition("=")
        mapping[old.strip()] = new.strip()
    return mapping


def run_rename(args: argparse.Namespace) -> int:
    source = load_from_file(args.file)
    mapping = _parse_renames(args.renames)

    new_env, result = rename_keys(source.data, mapping, overwrite=args.overwrite)

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(format_rename_text(result))

    return 1 if result.has_conflicts else 0


def main() -> None:  # pragma: no cover
    parser = build_rename_parser()
    args = parser.parse_args()
    sys.exit(run_rename(args))


if __name__ == "__main__":  # pragma: no cover
    main()
