"""Tests for envdiff.comparator_cli."""

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envdiff.comparator_cli import build_comparator_parser, run_comparator


def _make_source(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


class TestBuildComparatorParser:
    def test_requires_two_files(self):
        parser = build_comparator_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_two_files(self):
        parser = build_comparator_parser()
        args = parser.parse_args(["left.env", "right.env"])
        assert args.left == "left.env"
        assert args.right == "right.env"

    def test_default_format_is_text(self):
        parser = build_comparator_parser()
        args = parser.parse_args(["l", "r"])
        assert args.format == "text"

    def test_json_format_flag(self):
        parser = build_comparator_parser()
        args = parser.parse_args(["l", "r", "--format", "json"])
        assert args.format == "json"

    def test_no_redact_flag(self):
        parser = build_comparator_parser()
        args = parser.parse_args(["l", "r", "--no-redact"])
        assert args.no_redact is True

    def test_include_unchanged_flag(self):
        parser = build_comparator_parser()
        args = parser.parse_args(["l", "r", "--all"])
        assert args.include_unchanged is True


class TestRunComparator:
    def _args(self, left, right, fmt="text", no_redact=False, include_unchanged=False):
        import argparse
        ns = argparse.Namespace(
            left=str(left),
            right=str(right),
            format=fmt,
            no_redact=no_redact,
            include_unchanged=include_unchanged,
        )
        return ns

    def test_returns_zero_when_no_differences(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "KEY=value\n")
        g = _make_source(tmp_path, "b.env", "KEY=value\n")
        out = io.StringIO()
        code = run_comparator(self._args(f, g), out=out)
        assert code == 0

    def test_returns_one_when_differences_exist(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "KEY=old\n")
        g = _make_source(tmp_path, "b.env", "KEY=new\n")
        out = io.StringIO()
        code = run_comparator(self._args(f, g), out=out)
        assert code == 1

    def test_text_output_contains_key(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "APP_ENV=staging\n")
        g = _make_source(tmp_path, "b.env", "APP_ENV=prod\n")
        out = io.StringIO()
        run_comparator(self._args(f, g), out=out)
        assert "APP_ENV" in out.getvalue()

    def test_json_output_is_valid(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "K=1\n")
        g = _make_source(tmp_path, "b.env", "K=2\n")
        out = io.StringIO()
        run_comparator(self._args(f, g, fmt="json"), out=out)
        data = json.loads(out.getvalue())
        assert "rows" in data

    def test_missing_file_returns_one(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "K=v\n")
        out = io.StringIO()
        code = run_comparator(
            self._args(f, tmp_path / "missing.env"), out=out
        )
        assert code == 1

    def test_no_redact_shows_sensitive_value(self, tmp_path):
        f = _make_source(tmp_path, "a.env", "DB_PASSWORD=secret\n")
        g = _make_source(tmp_path, "b.env", "DB_PASSWORD=secret\n")
        out = io.StringIO()
        run_comparator(
            self._args(f, g, no_redact=True, include_unchanged=True), out=out
        )
        assert "secret" in out.getvalue()
