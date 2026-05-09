"""Tests for envdiff.env_differ_matrix."""

import pytest

from envdiff.env_differ_matrix import (
    DiffMatrix,
    MatrixRow,
    build_diff_matrix,
    format_matrix_text,
)
from envdiff.loader import EnvSource


def _src(name: str, data: dict) -> EnvSource:
    return EnvSource(name=name, data=data)


# ---------------------------------------------------------------------------
# MatrixRow
# ---------------------------------------------------------------------------

class TestMatrixRow:
    def test_uniform_when_all_same(self):
        row = MatrixRow(key="K", values={"a": "1", "b": "1"})
        assert row.is_uniform() is True

    def test_not_uniform_when_different(self):
        row = MatrixRow(key="K", values={"a": "1", "b": "2"})
        assert row.is_uniform() is False

    def test_uniform_ignores_missing_values(self):
        # present values are all "x", so uniform
        row = MatrixRow(key="K", values={"a": "x", "b": None})
        assert row.is_uniform() is True

    def test_complete_when_no_none(self):
        row = MatrixRow(key="K", values={"a": "1", "b": "2"})
        assert row.is_complete() is True

    def test_not_complete_when_missing(self):
        row = MatrixRow(key="K", values={"a": "1", "b": None})
        assert row.is_complete() is False

    def test_as_dict_has_expected_keys(self):
        row = MatrixRow(key="K", values={"a": "1"})
        d = row.as_dict()
        assert set(d) == {"key", "sensitive", "uniform", "complete", "values"}

    def test_sensitive_value_is_redacted_in_as_dict(self):
        row = MatrixRow(key="PASSWORD", values={"a": "secret"}, sensitive=True)
        d = row.as_dict()
        assert d["values"]["a"] != "secret"

    def test_non_sensitive_value_is_plain_in_as_dict(self):
        row = MatrixRow(key="HOST", values={"a": "localhost"}, sensitive=False)
        d = row.as_dict()
        assert d["values"]["a"] == "localhost"


# ---------------------------------------------------------------------------
# build_diff_matrix
# ---------------------------------------------------------------------------

class TestBuildDiffMatrix:
    def test_empty_sources_returns_empty_matrix(self):
        matrix = build_diff_matrix([])
        assert matrix.env_names == []
        assert matrix.rows == []

    def test_env_names_preserved(self):
        matrix = build_diff_matrix([_src("staging", {}), _src("prod", {})])
        assert matrix.env_names == ["staging", "prod"]

    def test_all_keys_collected(self):
        a = _src("a", {"FOO": "1", "BAR": "2"})
        b = _src("b", {"BAR": "2", "BAZ": "3"})
        matrix = build_diff_matrix([a, b])
        keys = [r.key for r in matrix.rows]
        assert "FOO" in keys and "BAR" in keys and "BAZ" in keys

    def test_missing_key_is_none(self):
        a = _src("a", {"ONLY_A": "yes"})
        b = _src("b", {})
        matrix = build_diff_matrix([a, b])
        row = next(r for r in matrix.rows if r.key == "ONLY_A")
        assert row.values["b"] is None

    def test_has_differences_true_when_values_differ(self):
        a = _src("a", {"X": "1"})
        b = _src("b", {"X": "2"})
        matrix = build_diff_matrix([a, b])
        assert matrix.has_differences is True

    def test_has_differences_false_when_identical(self):
        a = _src("a", {"X": "1"})
        b = _src("b", {"X": "1"})
        matrix = build_diff_matrix([a, b])
        assert matrix.has_differences is False

    def test_sensitive_key_flagged(self):
        a = _src("a", {"DB_PASSWORD": "s3cr3t"})
        b = _src("b", {"DB_PASSWORD": "other"})
        matrix = build_diff_matrix([a, b], redact=True)
        row = matrix.rows[0]
        assert row.sensitive is True

    def test_redact_false_does_not_flag_sensitive(self):
        a = _src("a", {"API_SECRET": "x"})
        matrix = build_diff_matrix([a], redact=False)
        assert matrix.rows[0].sensitive is False

    def test_differing_rows_excludes_uniform_complete(self):
        a = _src("a", {"SAME": "v", "DIFF": "1"})
        b = _src("b", {"SAME": "v", "DIFF": "2"})
        matrix = build_diff_matrix([a, b])
        diff_keys = [r.key for r in matrix.differing_rows()]
        assert "DIFF" in diff_keys
        assert "SAME" not in diff_keys

    def test_uniform_rows_includes_matching(self):
        a = _src("a", {"SAME": "v", "DIFF": "1"})
        b = _src("b", {"SAME": "v", "DIFF": "2"})
        matrix = build_diff_matrix([a, b])
        uniform_keys = [r.key for r in matrix.uniform_rows()]
        assert "SAME" in uniform_keys


# ---------------------------------------------------------------------------
# format_matrix_text
# ---------------------------------------------------------------------------

class TestFormatMatrixText:
    def test_no_differences_returns_message(self):
        a = _src("a", {"K": "1"})
        b = _src("b", {"K": "1"})
        matrix = build_diff_matrix([a, b])
        out = format_matrix_text(matrix)
        assert "identical" in out.lower()

    def test_output_contains_key_name(self):
        a = _src("a", {"MY_KEY": "foo"})
        b = _src("b", {"MY_KEY": "bar"})
        matrix = build_diff_matrix([a, b])
        out = format_matrix_text(matrix)
        assert "MY_KEY" in out

    def test_output_contains_env_names(self):
        a = _src("staging", {"X": "1"})
        b = _src("prod", {"X": "2"})
        matrix = build_diff_matrix([a, b])
        out = format_matrix_text(matrix)
        assert "staging" in out and "prod" in out

    def test_show_all_includes_uniform_rows(self):
        a = _src("a", {"SAME": "v"})
        b = _src("b", {"SAME": "v"})
        matrix = build_diff_matrix([a, b])
        out = format_matrix_text(matrix, show_all=True)
        assert "SAME" in out
