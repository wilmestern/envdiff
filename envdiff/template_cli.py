"""CLI entry point for env template generation."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.loader import load_from_file, load_from_string
from envdiff.env_templater import build_template, render_template_dotenv


def build_template_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-template",
        description="Generate a .env template from an existing env file.",
    )
    parser.add_argument("file", help="Path to .env file")
    parser.add_argument(
        "--name",
        default=None,
        help="Template name (defaults to filename)",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "--required",
        nargs="*",
        metavar="KEY",
        help="Keys to mark as required (default: all)",
    )
    return parser


def run_template(args: argparse.Namespace, out=sys.stdout) -> int:
    source = load_from_file(args.file)
    name = args.name or args.file
    template = build_template(name, dict(source), required_keys=args.required)

    if args.format == "json":
        out.write(json.dumps(template.as_dict(), indent=2))
        out.write("\n")
    else:
        out.write(render_template_dotenv(template))

    return 0


def main() -> None:  # pragma: no cover
    parser = build_template_parser()
    args = parser.parse_args()
    sys.exit(run_template(args))


if __name__ == "__main__":  # pragma: no cover
    main()
