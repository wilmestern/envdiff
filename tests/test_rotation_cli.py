"""Tests for envdiff.rotation_cli."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from envdiff.rotation_cli import build_rotation_parser, run_rotation, _format_report_text
from envdiff.env_rotator import RotationEntry, RotationReport


class TestBuildRotationParser:
    def test_requires_file_argument(self):
        p = build_rotation_parser()
        with pytest.raises(SystemExit):
            p.parse_args([])

    def test_requires_baseline_option(self):
        p = build_rotation_parser()
        with pytest.raises(SystemExit):
            p.parse_args(["some.env"])

    def test_parses_file_and_baseline(self):
        p = build_rotation_parser()
        args = p.parse_args(["prod.env", "--baseline", "prod"])
        assert args.file == "prod.env"
        assert args.baseline == "prod"

    def test_default_format_is_text(self):
        p = build_rotation_parser()
        args = p.parse_args(["f.env", "--baseline", "b"])
        assert args.format == "text"

    def test_json_format_accepted(self):
        p = build_rotation_parser()
        args = p.parse_args(["f.env", "--baseline", "b", "--format", "json"])
        assert args.format == "json"

    def test_sensitive_only_flag(self):
        p = build_rotation_parser()
        args = p.parse_args(["f.env", "--baseline", "b", "--sensitive-only"])
        assert args.sensitive_only is True


class TestFormatReportText:
    def test_no_changes_message(self):
        r = RotationReport(name="prod")
        text = _format_report_text(r)
        assert "No rotations detected" in text

    def test_rotated_keys_listed(self):
        r = RotationReport(name="prod", rotated=[RotationEntry("DB_PASS", "a", "b", sensitive=True)])
        text = _format_report_text(r)
        assert "DB_PASS" in text
        assert "[sensitive]" in text

    def test_added_keys_listed(self):
        r = RotationReport(name="prod", added=["NEW_KEY"])
        text = _format_report_text(r)
        assert "NEW_KEY" in text
        assert "+" in text

    def test_removed_keys_listed(self):
        r = RotationReport(name="prod", removed=["OLD_KEY"])
        text = _format_report_text(r)
        assert "OLD_KEY" in text
        assert "-" in text


class TestRunRotation:
    def _make_env_file(self, content: str):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False)
        f.write(content)
        f.flush()
        return f.name

    def test_returns_1_when_baseline_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._make_env_file("HOST=prod\n")
            try:
                result = run_rotation([env_file, "--baseline", "missing", "--store-dir", tmpdir])
                assert result == 1
            finally:
                os.unlink(env_file)

    def test_returns_0_when_no_rotations(self, capsys):
        from envdiff.baseline import Baseline
        from envdiff.baseline_store import BaselineStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir)
            store.save(Baseline(name="prod", data={"HOST": "same"}))
            env_file = self._make_env_file("HOST=same\n")
            try:
                result = run_rotation([env_file, "--baseline", "prod", "--store-dir", tmpdir])
                assert result == 0
            finally:
                os.unlink(env_file)

    def test_returns_1_when_rotations_found(self, capsys):
        from envdiff.baseline import Baseline
        from envdiff.baseline_store import BaselineStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir)
            store.save(Baseline(name="prod", data={"HOST": "old"}))
            env_file = self._make_env_file("HOST=new\n")
            try:
                result = run_rotation([env_file, "--baseline", "prod", "--store-dir", tmpdir])
                assert result == 1
            finally:
                os.unlink(env_file)

    def test_json_output_is_valid(self, capsys):
        from envdiff.baseline import Baseline
        from envdiff.baseline_store import BaselineStore

        with tempfile.TemporaryDirectory() as tmpdir:
            store = BaselineStore(tmpdir)
            store.save(Baseline(name="prod", data={"HOST": "old"}))
            env_file = self._make_env_file("HOST=new\n")
            try:
                run_rotation([env_file, "--baseline", "prod", "--store-dir", tmpdir, "--format", "json"])
                captured = capsys.readouterr()
                data = json.loads(captured.out)
                assert "rotated" in data
            finally:
                os.unlink(env_file)
