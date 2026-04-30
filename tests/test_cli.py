"""Tests for envdiff.cli module."""

import json
import pytest
from unittest.mock import patch

from envdiff.cli import build_parser, run


class TestBuildParser:
    def test_requires_two_files(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_two_files(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert args.file_a == "a.env"
        assert args.file_b == "b.env"

    def test_default_format_is_text(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert args.format == "text"

    def test_json_format(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env", "--format", "json"])
        assert args.format == "json"

    def test_show_unchanged_flag(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env", "--show-unchanged"])
        assert args.show_unchanged is True

    def test_no_redact_flag(self):
        parser = build_parser()
        args = parser.parse_args(["a.env", "b.env", "--no-redact"])
        assert args.no_redact is True


class TestRun:
    def test_missing_file_returns_1(self, tmp_path):
        result = run([str(tmp_path / "missing.env"), str(tmp_path / "also.env")])
        assert result == 1

    def test_text_output(self, tmp_path):
        a = tmp_path / "staging.env"
        b = tmp_path / "prod.env"
        a.write_text("HOST=localhost\nPORT=5432\n")
        b.write_text("HOST=prod.example.com\nPORT=5432\n")
        result = run([str(a), str(b)])
        assert result == 0

    def test_json_output(self, tmp_path, capsys):
        a = tmp_path / "staging.env"
        b = tmp_path / "prod.env"
        a.write_text("HOST=localhost\n")
        b.write_text("HOST=prod.example.com\n")
        result = run([str(a), str(b), "--format", "json"])
        assert result == 0
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert "entries" in parsed

    def test_redaction_applied_by_default(self, tmp_path, capsys):
        a = tmp_path / "a.env"
        b = tmp_path / "b.env"
        a.write_text("SECRET_KEY=mysecret\n")
        b.write_text("SECRET_KEY=othersecret\n")
        run([str(a), str(b)])
        captured = capsys.readouterr()
        assert "mysecret" not in captured.out
        assert "othersecret" not in captured.out

    def test_no_redact_flag_shows_values(self, tmp_path, capsys):
        a = tmp_path / "a.env"
        b = tmp_path / "b.env"
        a.write_text("SECRET_KEY=mysecret\n")
        b.write_text("SECRET_KEY=othersecret\n")
        run([str(a), str(b), "--no-redact"])
        captured = capsys.readouterr()
        assert "mysecret" in captured.out or "othersecret" in captured.out
