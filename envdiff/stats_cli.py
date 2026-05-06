"""CLI helper that prints statistics for one or two env files."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from envdiff.loader import load_from_file, load_from_string
from envdiff.env_stats import compute_stats, format_stats_text


def build_stats_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-stats",
        description="Show statistics for one or two .env files.",
    )
    parser.add_argument("files", nargs="+", metavar="FILE", help=".env file(s) to analyse")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    return parser


def _stats_for_file(path: str) -> dict:
    source = load_from_file(path)
    stats = compute_stats(source.data)
    return {"name": source.name, "stats": stats}


def run_stats(argv: Optional[List[str]] = None) -> int:
    parser = build_stats_parser()
    args = parser.parse_args(argv)

    results = []
    for path in args.files:
        try:
            entry = _stats_for_file(path)
        except FileNotFoundError:
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        except Exception as exc:  # pragma: no cover
            print(f"error: {exc}", file=sys.stderr)
            return 1
        results.append(entry)

    if args.format == "json":
        payload = [
            {"name": r["name"], "stats": r["stats"].as_dict()}
            for r in results
        ]
        print(json.dumps(payload, indent=2))
    else:
        for r in results:
            print(f"=== {r['name']} ===")
            print(format_stats_text(r["stats"]))
            print()

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_stats())


if __name__ == "__main__":  # pragma: no cover
    main()
