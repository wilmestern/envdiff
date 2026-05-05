"""Tests for envdiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.differ import DiffEntry, DiffResult, DiffStatus
from envdiff.exporter import export_dotenv_patch, export_json, export_text, _quote


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _entry(key: str, status: DiffStatus, left=None, right=None) -> DiffEntry:
    return DiffEntry(key=key, status=status, left_value=left, right_value=right)


def _result(*entries: DiffEntry) -> DiffResult:
    return DiffResult(entries=list(entries))


# ---------------------------------------------------------------------------
# export_text
# ---------------------------------------------------------------------------

class TestExportText:
    def test_creates_file(self, tmp_path: Path):
        result = _result(_entry("FOO", DiffStatus.ADDED, right="bar"))
        out = tmp_path / "diff.txt"
        n = export_text(result, out)
        assert out.exists()
        assert n > 0

    def test_content_contains_key(self, tmp_path: Path):
        result = _result(_entry("MY_KEY", DiffStatus.ADDED, right="v"))
        out = tmp_path / "diff.txt"
        export_text(result, out)
        assert "MY_KEY" in out.read_text()

    def test_creates_parent_dirs(self, tmp_path: Path):
        out = tmp_path / "nested" / "deep" / "diff.txt"
        result = _result(_entry("X", DiffStatus.REMOVED, left="1"))
        export_text(result, out)
        assert out.exists()


# ---------------------------------------------------------------------------
# export_json
# ---------------------------------------------------------------------------

class TestExportJson:
    def test_creates_valid_json(self, tmp_path: Path):
        result = _result(
            _entry("A", DiffStatus.ADDED, right="1"),
            _entry("B", DiffStatus.REMOVED, left="2"),
        )
        out = tmp_path / "diff.json"
        export_json(result, out)
        data = json.loads(out.read_text())
        assert isinstance(data, (list, dict))

    def test_returns_byte_count(self, tmp_path: Path):
        result = _result(_entry("K", DiffStatus.CHANGED, left="old", right="new"))
        out = tmp_path / "diff.json"
        n = export_json(result, out)
        assert n == out.stat().st_size


# ---------------------------------------------------------------------------
# export_dotenv_patch
# ---------------------------------------------------------------------------

class TestExportDotenvPatch:
    def test_added_key_present(self, tmp_path: Path):
        result = _result(_entry("NEW_VAR", DiffStatus.ADDED, right="hello"))
        out = tmp_path / "patch.env"
        export_dotenv_patch(result, out)
        content = out.read_text()
        assert "NEW_VAR=hello" in content

    def test_changed_key_uses_right_value(self, tmp_path: Path):
        result = _result(_entry("DB_URL", DiffStatus.CHANGED, left="old", right="new"))
        out = tmp_path / "patch.env"
        export_dotenv_patch(result, out)
        assert "DB_URL=new" in out.read_text()

    def test_removed_key_is_commented(self, tmp_path: Path):
        result = _result(_entry("GONE", DiffStatus.REMOVED, left="x"))
        out = tmp_path / "patch.env"
        export_dotenv_patch(result, out)
        assert "# REMOVED: GONE" in out.read_text()

    def test_unchanged_key_excluded(self, tmp_path: Path):
        result = _result(_entry("SAME", DiffStatus.UNCHANGED, left="v", right="v"))
        out = tmp_path / "patch.env"
        export_dotenv_patch(result, out)
        assert "SAME" not in out.read_text()


# ---------------------------------------------------------------------------
# _quote helper
# ---------------------------------------------------------------------------

class TestQuote:
    def test_simple_value_unchanged(self):
        assert _quote("simple") == "simple"

    def test_value_with_space_is_quoted(self):
        result = _quote("hello world")
        assert result.startswith('"') and result.endswith('"')

    def test_none_returns_empty_string(self):
        assert _quote(None) == ""

    def test_value_with_double_quote_escaped(self):
        result = _quote('say "hi"')
        assert '\\"' in result
