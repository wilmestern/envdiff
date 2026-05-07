"""Tests for envdiff.score_cli."""

import json
from unittest.mock import patch, MagicMock

import pytest

from envdiff.score_cli import build_score_parser, run_score
from envdiff.loader import EnvSource


def _make_source(name="staging", data=None):
    src = MagicMock(spec=EnvSource)
    src.name = name
    src.data = data or {"APP_ENV": "staging", "PORT": "8080"}
    return src


class TestBuildScoreParser:
    def test_requires_at_least_one_file(self):
        parser = build_score_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_single_file(self):
        parser = build_score_parser()
        args = parser.parse_args(["staging.env"])
        assert args.files == ["staging.env"]

    def test_parses_multiple_files(self):
        parser = build_score_parser()
        args = parser.parse_args(["a.env", "b.env"])
        assert len(args.files) == 2

    def test_default_format_is_text(self):
        parser = build_score_parser()
        args = parser.parse_args(["x.env"])
        assert args.format == "text"

    def test_json_format_accepted(self):
        parser = build_score_parser()
        args = parser.parse_args(["x.env", "--format", "json"])
        assert args.format == "json"

    def test_fail_below_defaults_to_none(self):
        parser = build_score_parser()
        args = parser.parse_args(["x.env"])
        assert args.fail_below is None

    def test_fail_below_parsed_as_float(self):
        parser = build_score_parser()
        args = parser.parse_args(["x.env", "--fail-below", "80"])
        assert args.fail_below == 80.0


class TestRunScore:
    def test_returns_zero_on_success(self, tmp_path):
        env_file = tmp_path / "staging.env"
        env_file.write_text("APP=prod\nPORT=8080\n")
        result = run_score([str(env_file)])
        assert result == 0

    def test_returns_two_for_missing_file(self):
        result = run_score(["nonexistent_file.env"])
        assert result == 2

    def test_text_output_contains_filename(self, tmp_path, capsys):
        env_file = tmp_path / "myenv.env"
        env_file.write_text("KEY=value\n")
        run_score([str(env_file)])
        captured = capsys.readouterr()
        assert "myenv" in captured.out

    def test_json_output_is_valid_json(self, tmp_path, capsys):
        env_file = tmp_path / "prod.env"
        env_file.write_text("DB=localhost\n")
        run_score([str(env_file), "--format", "json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert "score" in data[0]

    def test_fail_below_returns_one_when_score_low(self, tmp_path):
        env_file = tmp_path / "bad.env"
        # Many empty values to drive score down
        lines = "\n".join(f"KEY_{i}=" for i in range(20))
        env_file.write_text(lines)
        result = run_score([str(env_file), "--fail-below", "99"])
        assert result == 1

    def test_fail_below_returns_zero_when_score_meets_threshold(self, tmp_path):
        env_file = tmp_path / "good.env"
        env_file.write_text("APP=production\nPORT=443\n")
        result = run_score([str(env_file), "--fail-below", "50"])
        assert result == 0
