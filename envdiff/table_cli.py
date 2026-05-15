"""CLI entry point for the table formatter."""
from __future__ import annotations

import argparse
import json
import sys


def build_table_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-table",
        description="Render one or more .env files as an aligned table.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to include in the table (name=path or just path).",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        default=False,
        help="Show sensitive values in plain text (use with care).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _load_sources(file_args: list) -> dict:
    from envdiff.loader import load_from_file

    sources = {}
    for arg in file_args:
        if "=" in arg:
            name, path = arg.split("=", 1)
        else:
            path = arg
            name = path
        src = load_from_file(path, name=name)
        sources[src.name] = dict(src)
    return sources


def run_table(args: argparse.Namespace, out=None) -> int:
    from envdiff.env_formatter_table import build_table, format_table_text

    if out is None:
        out = sys.stdout

    try:
        sources = _load_sources(args.files)
    except (FileNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    redact = not args.no_redact
    rows = build_table(sources, redact=redact)

    if args.format == "json":
        json.dump([r.as_dict() for r in rows], out, indent=2)
        out.write("\n")
    else:
        out.write(format_table_text(rows))
        out.write("\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_table_parser()
    args = parser.parse_args()
    sys.exit(run_table(args))
