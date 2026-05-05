"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.exporter import export_dotenv_patch, export_json, export_text
from envdiff.formatter import format_json, format_text
from envdiff.loader import load_from_file, load_from_string


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare environment variable sets across configs with redaction support.",
    )
    parser.add_argument("left", help="Path to the first (source) .env file")
    parser.add_argument("right", help="Path to the second (target) .env file")
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
        help="Include unchanged keys in the output",
    )
    parser.add_argument(
        "--no-redact",
        action="store_true",
        default=False,
        help="Disable automatic redaction of sensitive values",
    )
    parser.add_argument(
        "--export",
        metavar="PATH",
        help="Write the diff to a file instead of (or in addition to) stdout",
    )
    parser.add_argument(
        "--export-format",
        choices=["text", "json", "dotenv"],
        default=None,
        help="Format for --export output (defaults to --format or 'dotenv' for .env paths)",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    left_source = load_from_file(args.left, redact=not args.no_redact)
    right_source = load_from_file(args.right, redact=not args.no_redact)

    result = diff_envs(left_source, right_source)

    # --- stdout output ---
    if args.format == "json":
        print(format_json(result, show_unchanged=args.show_unchanged))
    else:
        print(format_text(result, show_unchanged=args.show_unchanged))

    # --- optional file export ---
    if args.export:
        export_fmt = args.export_format
        if export_fmt is None:
            # Infer from extension or fall back to --format
            ext = Path(args.export).suffix.lower()
            if ext in (".env", ".patch"):
                export_fmt = "dotenv"
            else:
                export_fmt = args.format

        if export_fmt == "dotenv":
            export_dotenv_patch(result, args.export)
        elif export_fmt == "json":
            export_json(result, args.export, show_unchanged=args.show_unchanged)
        else:
            export_text(result, args.export, show_unchanged=args.show_unchanged)

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())
