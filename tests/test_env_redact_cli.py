"""Tests for envdiff.env_redact_cli."""

import io
import textwrap
from unittest.mock import patch, MagicMock

import pytest

from envdiff.env_redact_cli import build_redact_parser, run_redact


def _make_source(data: dict, name: str = "test.env"):
    src = MagicMock()
    src.data = data
    src.name = name
    return src


class TestBuildRedactParser:
    def test_requires_file_argument(self):
        parser = build_redact_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parses_file(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env"])
        assert args.file == "prod.env"

    def test_default_format_is_dotenv(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env"])
        assert args.format == "dotenv"

    def test_json_format(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env", "--format", "json"])
        assert args.format == "json"

    def test_default_placeholder(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env"])
        assert args.placeholder == "***"

    def test_custom_placeholder(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env", "--placeholder", "REDACTED"])
        assert args.placeholder == "REDACTED"

    def test_output_defaults_to_none(self):
        parser = build_redact_parser()
        args = parser.parse_args(["prod.env"])
        assert args.output is None


class TestRunRedact:
    def _args(self, file="prod.env", fmt="dotenv", placeholder="***", output=None):
        parser = build_redact_parser()
        argv = [file, "--format", fmt, "--placeholder", placeholder]
        if output:
            argv += ["--output", output]
        return parser.parse_args(argv)

    def test_returns_zero_on_success(self, tmp_path):
        env_file = tmp_path / "prod.env"
        env_file.write_text("APP_NAME=myapp\nDB_PASSWORD=secret\n")
        args = self._args(file=str(env_file))
        out = io.StringIO()
        assert run_redact(args, out=out) == 0

    def test_redacts_sensitive_key_in_dotenv(self, tmp_path):
        env_file = tmp_path / "prod.env"
        env_file.write_text("APP_NAME=myapp\nDB_PASSWORD=secret\n")
        args = self._args(file=str(env_file))
        out = io.StringIO()
        run_redact(args, out=out)
        result = out.getvalue()
        assert "APP_NAME=myapp" in result
        assert "secret" not in result
        assert "***" in result

    def test_json_format_output(self, tmp_path):
        env_file = tmp_path / "prod.env"
        env_file.write_text("API_KEY=abc123\nAPP=myapp\n")
        args = self._args(file=str(env_file), fmt="json")
        out = io.StringIO()
        run_redact(args, out=out)
        import json
        data = json.loads(out.getvalue())
        assert data["APP"] == "myapp"
        assert data["API_KEY"] == "***"

    def test_file_not_found_returns_one(self):
        args = self._args(file="nonexistent.env")
        out = io.StringIO()
        assert run_redact(args, out=out) == 1

    def test_writes_to_output_file(self, tmp_path):
        env_file = tmp_path / "prod.env"
        env_file.write_text("TOKEN=abc\nNAME=app\n")
        out_file = tmp_path / "redacted.env"
        args = self._args(file=str(env_file), output=str(out_file))
        result = run_redact(args)
        assert result == 0
        content = out_file.read_text()
        assert "NAME=app" in content
        assert "abc" not in content
