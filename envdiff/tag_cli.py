"""CLI entry point for the env-tagger feature."""

import argparse
import json
import sys

from envdiff.loader import load_from_file
from envdiff.env_tagger import tag_env, format_tagged_text


def build_tag_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-tag",
        description="Tag environment variables by category.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to tag.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--tag",
        nargs=2,
        metavar=("TAG", "KEYWORD"),
        action="append",
        dest="extra_tags",
        default=[],
        help="Extra tag pattern: --tag mytag myprefix (repeatable).",
    )
    return parser


def _build_extra_patterns(extra_tags) -> dict:
    patterns = {}
    for tag, keyword in extra_tags:
        patterns.setdefault(tag, []).append(keyword)
    return patterns


def run_tag(args: argparse.Namespace, out=sys.stdout) -> int:
    extra_patterns = _build_extra_patterns(args.extra_tags)
    results = []

    for path in args.files:
        try:
            source = load_from_file(path)
        except (OSError, ValueError) as exc:
            print(f"Error loading {path}: {exc}", file=sys.stderr)
            return 1
        tagged = tag_env(source.data, name=source.name, extra_patterns=extra_patterns or None)
        results.append(tagged)

    if args.format == "json":
        payload = [t.as_dict() for t in results]
        print(json.dumps(payload, indent=2), file=out)
    else:
        for tagged in results:
            print(format_tagged_text(tagged), file=out)
            print("", file=out)

    return 0


def main():
    parser = build_tag_parser()
    args = parser.parse_args()
    sys.exit(run_tag(args))


if __name__ == "__main__":
    main()
