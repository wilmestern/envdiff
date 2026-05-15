"""Tests for env_formatter_table and table_cli."""
from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import pytest

from envdiff.env_formatter_table import TableRow, build_table, format_table_text


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _envs():
    return {
        "staging": {"DB_HOST": "localhost", "SECRET_KEY": "s3cr3t", "PORT": "5432"},
        "prod": {"DB_HOST": "db.prod", "SECRET_KEY": "pr0ds3cr3t", "PORT": "5432"},
    }


# ---------------------------------------------------------------------------
# TableRow
# ---------------------------------------------------------------------------

class TestTableRow:
    def test_as_dict_has_expected_keys(self):
        row = TableRow(key="FOO", value="bar", source="staging")
        d = row.as_dict()
        assert set(d.keys()) == {"key", "value", "source", "sensitive"}

    def test_sensitive_defaults_to_false(self):
        row = TableRow(key="FOO", value="bar", source="staging")
        assert row.sensitive is False

    def test_repr_contains_key_and_source(self):
        row = TableRow(key="FOO", value="bar", source="prod")
        assert "FOO" in repr(row)
        assert "prod" in repr(row)


# ---------------------------------------------------------------------------
# build_table
# ---------------------------------------------------------------------------

class TestBuildTable:
    def test_returns_list_of_table_rows(self):
        rows = build_table({"staging": {"FOO": "bar"}})
        assert all(isinstance(r, TableRow) for r in rows)

    def test_row_count_matches_total_keys(self):
        rows = build_table(_envs())
        # 2 sources × 3 keys = 6 rows
        assert len(rows) == 6

    def test_sorted_by_key_then_source(self):
        rows = build_table(_envs())
        pairs = [(r.key, r.source) for r in rows]
        assert pairs == sorted(pairs)

    def test_redacts_sensitive_values_by_default(self):
        rows = build_table({"s": {"SECRET_KEY": "topsecret"}})
        row = rows[0]
        assert row.value != "topsecret"
        assert row.sensitive is True

    def test_no_redact_shows_plain_value(self):
        rows = build_table({"s": {"SECRET_KEY": "topsecret"}}, redact=False)
        assert rows[0].value == "topsecret"

    def test_non_sensitive_value_unchanged(self):
        rows = build_table({"s": {"PORT": "5432"}})
        assert rows[0].value == "5432"
        assert rows[0].sensitive is False


# ---------------------------------------------------------------------------
# format_table_text
# ---------------------------------------------------------------------------

class TestFormatTableText:
    def test_empty_rows_returns_placeholder(self):
        assert format_table_text([]) == "(no entries)"

    def test_output_contains_header(self):
        rows = build_table({"s": {"FOO": "bar"}})
        text = format_table_text(rows)
        assert "KEY" in text
        assert "SOURCE" in text
        assert "VALUE" in text

    def test_output_contains_key(self):
        rows = build_table({"s": {"MY_KEY": "val"}})
        assert "MY_KEY" in format_table_text(rows)

    def test_separator_line_present(self):
        rows = build_table({"s": {"X": "1"}})
        lines = format_table_text(rows).splitlines()
        assert any(set(line.strip()) == {"-"} for line in lines)


# ---------------------------------------------------------------------------
# table_cli
# ---------------------------------------------------------------------------

class TestBuildTableParser:
    def test_requires_at_least_one_file(self):
        from envdiff.table_cli import build_table_parser
        parser = build_table_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_default_format_is_text(self):
        from envdiff.table_cli import build_table_parser
        parser = build_table_parser()
        args = parser.parse_args(["file.env"])
        assert args.format == "text"

    def test_no_redact_flag(self):
        from envdiff.table_cli import build_table_parser
        parser = build_table_parser()
        args = parser.parse_args(["--no-redact", "file.env"])
        assert args.no_redact is True


class TestRunTable:
    def _make_source(self, name, data):
        from envdiff.loader import EnvSource
        return EnvSource(name=name, data=data)

    def test_text_output_written(self):
        from envdiff.table_cli import build_table_parser, run_table
        src = self._make_source("staging", {"FOO": "bar"})
        parser = build_table_parser()
        args = parser.parse_args(["staging=staging.env"])
        out = StringIO()
        with patch("envdiff.table_cli._load_sources", return_value={"staging": {"FOO": "bar"}}):
            rc = run_table(args, out=out)
        assert rc == 0
        assert "FOO" in out.getvalue()

    def test_json_output_is_valid(self):
        from envdiff.table_cli import build_table_parser, run_table
        parser = build_table_parser()
        args = parser.parse_args(["--format", "json", "staging.env"])
        out = StringIO()
        with patch("envdiff.table_cli._load_sources", return_value={"staging": {"X": "1"}}):
            rc = run_table(args, out=out)
        assert rc == 0
        data = json.loads(out.getvalue())
        assert isinstance(data, list)
        assert data[0]["key"] == "X"

    def test_missing_file_returns_error_code(self):
        from envdiff.table_cli import build_table_parser, run_table
        parser = build_table_parser()
        args = parser.parse_args(["nonexistent.env"])
        out = StringIO()
        with patch("envdiff.table_cli._load_sources", side_effect=FileNotFoundError("not found")):
            rc = run_table(args, out=out)
        assert rc == 1
