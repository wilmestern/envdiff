"""CLI entry point for the env linter."""

import argparse
import json
import sys

from envdiff.loader import load_from_file, load_from_string
from envdiff.env_linter import lint_env, format_lint_text


def build_lint_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-lint",
        description="Lint .env files for common issues.",
    )
    parser.add_argument("files", nargs="+", metavar="FILE", help="One or more .env files to lint.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any warnings exist.",
    )
    return parser


def _lint_file(path: str):
    source = load_from_file(path)
    return source.name, lint_env(source.data)


def run_lint(args: argparse.Namespace) -> int:
    results = []
    for filepath in args.files:
        name, result = _lint_file(filepath)
        results.append((name, result))

    if args.format == "json":
        output = {
            name: result.as_dict() for name, result in results
        }
        print(json.dumps(output, indent=2))
    else:
        for name, result in results:
            print(format_lint_text(result, name=name))
            print()

    has_errors = any(r.errors for _, r in results)
    has_warnings = any(r.warnings for _, r in results)

    if has_errors:
        return 2
    if args.strict and has_warnings:
        return 1
    return 0


def main():  # pragma: no cover
    parser = build_lint_parser()
    args = parser.parse_args()
    sys.exit(run_lint(args))
