"""CLI for redacting sensitive values in an env file and writing the result."""

import argparse
import json
import sys

from envdiff.loader import load_from_file, load_from_string
from envdiff.redactor import redact_env


def build_redact_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-redact",
        description="Redact sensitive values from an env file.",
    )
    parser.add_argument("file", help="Path to the .env file to redact")
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        help="Output format (default: dotenv)",
    )
    parser.add_argument(
        "--placeholder",
        default="***",
        help="Placeholder for redacted values (default: ***)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write output to this file instead of stdout",
    )
    return parser


def _format_dotenv(data: dict, placeholder: str) -> str:
    redacted = redact_env(data, placeholder=placeholder)
    lines = [f"{k}={v}" for k, v in sorted(redacted.items())]
    return "\n".join(lines) + "\n"


def _format_json(data: dict, placeholder: str) -> str:
    redacted = redact_env(data, placeholder=placeholder)
    return json.dumps(dict(sorted(redacted.items())), indent=2) + "\n"


def run_redact(args: argparse.Namespace, out=None) -> int:
    if out is None:
        out = sys.stdout

    try:
        source = load_from_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        content = _format_json(source.data, args.placeholder)
    else:
        content = _format_dotenv(source.data, args.placeholder)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(content)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    else:
        out.write(content)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_redact_parser()
    args = parser.parse_args()
    sys.exit(run_redact(args))
