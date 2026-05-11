"""CLI entry-point for the env-profiler feature."""

import argparse
import json
import sys

from envdiff.loader import load_from_file, load_from_string
from envdiff.env_profiler import profile_env, format_profile_text


def build_profile_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-profile",
        description="Profile one or more .env files and report statistics.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="Path(s) to .env file(s) to profile.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _profile_file(path: str):
    source = load_from_file(path)
    return profile_env(name=source.name, env=source.data)


def run_profile(args: argparse.Namespace, out=sys.stdout) -> int:
    profiles = [_profile_file(f) for f in args.files]

    if args.format == "json":
        payload = [p.as_dict() for p in profiles]
        out.write(json.dumps(payload, indent=2))
        out.write("\n")
    else:
        for profile in profiles:
            out.write(format_profile_text(profile))
            out.write("\n")

    return 0


def main() -> None:  # pragma: no cover
    parser = build_profile_parser()
    args = parser.parse_args()
    sys.exit(run_profile(args))
