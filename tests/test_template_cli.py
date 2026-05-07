"""Tests for envdiff.template_cli."""

from __future__ import annotations

import io
import json
import textwrap
from unittest.mock import patch, MagicMock

import pytest

from envdiff.template_cli import build_template_parser, run_template
from envdiff.loader import EnvSource


def _make_source(data: dict, name: str = "test.env") -> EnvSource:
    return EnvSource(name=name, data=data)


class TestBuildTemplateParser:
    def test_requires_file_argument(self):
        parser = build_template_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_file(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env"])
        assert args.file == "staging.env"

    def test_default_format_is_dotenv(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env"])
        assert args.format == "dotenv"

    def test_json_format_accepted(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env", "--format", "json"])
        assert args.format == "json"

    def test_name_defaults_to_none(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env"])
        assert args.name is None

    def test_name_can_be_set(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env", "--name", "my-template"])
        assert args.name == "my-template"

    def test_required_keys_accepted(self):
        parser = build_template_parser()
        args = parser.parse_args(["staging.env", "--required", "FOO", "BAR"])
        assert args.required == ["FOO", "BAR"]


class TestRunTemplate:
    def _run(self, data: dict, extra_args: list = None, name: str = "test.env") -> str:
        source = _make_source(data, name)
        parser = build_template_parser()
        file_args = [name] + (extra_args or [])
        args = parser.parse_args(file_args)
        out = io.StringIO()
        with patch("envdiff.template_cli.load_from_file", return_value=source):
            run_template(args, out=out)
        return out.getvalue()

    def test_dotenv_output_contains_key(self):
        result = self._run({"APP_HOST": "localhost"})
        assert "APP_HOST=" in result

    def test_dotenv_output_contains_placeholder(self):
        result = self._run({"APP_HOST": "localhost"})
        assert "<app_host>" in result

    def test_json_output_is_valid_json(self):
        result = self._run({"APP_HOST": "x"}, extra_args=["--format", "json"])
        data = json.loads(result)
        assert "entries" in data

    def test_json_output_has_name(self):
        result = self._run({"X": "1"}, extra_args=["--format", "json"], name="prod.env")
        data = json.loads(result)
        assert data["name"] == "prod.env"

    def test_returns_zero_on_success(self):
        source = _make_source({"FOO": "bar"})
        parser = build_template_parser()
        args = parser.parse_args(["test.env"])
        out = io.StringIO()
        with patch("envdiff.template_cli.load_from_file", return_value=source):
            code = run_template(args, out=out)
        assert code == 0

    def test_custom_name_used_in_output(self):
        result = self._run(
            {"X": "1"},
            extra_args=["--name", "my-template"],
        )
        assert "my-template" in result
