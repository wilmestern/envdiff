"""CLI entry point for the env-annotator tool."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.env_annotator import annotate_env, format_annotations_text
from envdiff.loader import load_from_file


def build_annotator_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-annotate",
        description="Annotate environment variables with metadata tags.",
    )
    parser.add_argument("file", help="Path to .env file to annotate")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--tag",
        metavar="NAME=SUBSTR",
        action="append",
        default=[],
        dest="extra_tags",
        help="Extra annotation rule as NAME=SUBSTR (may be repeated)",
    )
    return parser


def _parse_extra_tags(raw: list[str]) -> dict[str, str]:
    rules: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid --tag value {item!r}; expected NAME=SUBSTR")
        name, _, substr = item.partition("=")
        rules[name.strip()] = substr.strip()
    return rules


def run_annotator(args: argparse.Namespace, out=sys.stdout) -> int:
    try:
        source = load_from_file(args.file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        return 1

    try:
        extra_rules = _parse_extra_tags(args.extra_tags)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    entries = annotate_env(source.data, extra_rules=extra_rules or None)

    if args.format == "json":
        payload = [e.as_dict() for e in entries]
        print(json.dumps(payload, indent=2), file=out)
    else:
        print(f"Annotations for {source.name}:", file=out)
        print(format_annotations_text(entries), file=out)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_annotator_parser()
    args = parser.parse_args()
    sys.exit(run_annotator(args))
