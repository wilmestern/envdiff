"""Tests for envdiff.alias_cli."""

import json
from unittest.mock import patch, MagicMock

import pytest

from envdiff.alias_cli import build_alias_parser, run_alias, _parse_aliases
from envdiff.loader import EnvSource


def _make_source(data=None):
    return EnvSource(name="test.env", data=data or {"DB_URL": "postgres://localhost", "PORT": "5432"})


class TestBuildAliasParser:
    def test_requires_file_argument(self):
        parser = build_alias_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_file(self):
        parser = build_alias_parser()
        args = parser.parse_args(["staging.env"])
        assert args.file == "staging.env"

    def test_default_format_is_text(self):
        parser = build_alias_parser()
        args = parser.parse_args(["staging.env"])
        assert args.format == "text"

    def test_json_format_accepted(self):
        parser = build_alias_parser()
        args = parser.parse_args(["staging.env", "--format", "json"])
        assert args.format == "json"

    def test_alias_flag_repeatable(self):
        parser = build_alias_parser()
        args = parser.parse_args(["f.env", "--alias", "A=B", "--alias", "C=D"])
        assert args.aliases == ["A=B", "C=D"]

    def test_overwrite_flag_default_false(self):
        parser = build_alias_parser()
        args = parser.parse_args(["f.env"])
        assert args.overwrite is False

    def test_overwrite_flag_sets_true(self):
        parser = build_alias_parser()
        args = parser.parse_args(["f.env", "--overwrite"])
        assert args.overwrite is True


class TestParseAliases:
    def test_parses_single_alias(self):
        result = _parse_aliases(["DATABASE_URL=DB_URL"])
        assert result == {"DATABASE_URL": "DB_URL"}

    def test_parses_multiple_aliases(self):
        result = _parse_aliases(["A=B", "C=D"])
        assert result == {"A": "B", "C": "D"}

    def test_raises_on_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid alias format"):
            _parse_aliases(["NODIVIDER"])

    def test_empty_list_returns_empty_dict(self):
        assert _parse_aliases([]) == {}


class TestRunAlias:
    def _run(self, argv, source=None):
        src = source or _make_source()
        with patch("envdiff.alias_cli.load_from_file", return_value=src):
            return run_alias(argv)

    def test_returns_zero_on_success(self):
        code = self._run(["staging.env", "--alias", "DATABASE_URL=DB_URL"])
        assert code == 0

    def test_returns_two_on_bad_alias_format(self):
        with patch("envdiff.alias_cli.load_from_file", return_value=_make_source()):
            code = run_alias(["staging.env", "--alias", "BADALIAS"])
        assert code == 2

    def test_json_output_is_valid(self, capsys):
        self._run(["staging.env", "--alias", "DATABASE_URL=DB_URL", "--format", "json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "applied" in data
        assert "skipped" in data

    def test_text_output_shows_applied(self, capsys):
        self._run(["staging.env", "--alias", "DATABASE_URL=DB_URL"])
        out = capsys.readouterr().out
        assert "DATABASE_URL" in out

    def test_no_changes_message_when_nothing_applied(self, capsys):
        self._run(["staging.env", "--alias", "DATABASE_URL=MISSING"])
        out = capsys.readouterr().out
        assert "No aliases applied" in out
