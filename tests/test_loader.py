"""Tests for envdiff.loader module."""

import pytest
from pathlib import Path

from envdiff.loader import (
    EnvSource,
    load_from_file,
    load_from_string,
    load_from_mapping,
    load_from_directory,
)


class TestEnvSource:
    def test_name_and_data(self):
        src = EnvSource(name="staging", data={"KEY": "value"})
        assert src.name == "staging"
        assert src.data == {"KEY": "value"}

    def test_len(self):
        src = EnvSource(name="test", data={"A": "1", "B": "2"})
        assert len(src) == 2

    def test_repr(self):
        src = EnvSource(name="prod", data={"X": "y"})
        assert "prod" in repr(src)
        assert "X" in repr(src)


class TestLoadFromString:
    def test_basic(self):
        src = load_from_string("FOO=bar\nBAZ=qux", name="test")
        assert src.name == "test"
        assert src.data == {"FOO": "bar", "BAZ": "qux"}

    def test_default_name(self):
        src = load_from_string("A=1")
        assert src.name == "<string>"

    def test_empty_string(self):
        src = load_from_string("")
        assert src.data == {}


class TestLoadFromMapping:
    def test_basic(self):
        src = load_from_mapping({"KEY": "val"}, name="mymap")
        assert src.name == "mymap"
        assert src.data["KEY"] == "val"

    def test_default_name(self):
        src = load_from_mapping({})
        assert src.name == "<mapping>"

    def test_strips_whitespace(self):
        src = load_from_mapping({"KEY": "  spaced  "})
        assert src.data["KEY"] == "spaced"


class TestLoadFromFile:
    def test_loads_file(self, tmp_path):
        env_file = tmp_path / "staging.env"
        env_file.write_text("HOST=localhost\nPORT=5432\n")
        src = load_from_file(env_file)
        assert src.name == "staging.env"
        assert src.data["HOST"] == "localhost"
        assert src.data["PORT"] == "5432"

    def test_custom_name(self, tmp_path):
        env_file = tmp_path / "prod.env"
        env_file.write_text("X=1")
        src = load_from_file(env_file, name="production")
        assert src.name == "production"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_from_file(tmp_path / "nonexistent.env")

    def test_directory_raises(self, tmp_path):
        with pytest.raises(ValueError):
            load_from_file(tmp_path)


class TestLoadFromDirectory:
    def test_loads_multiple_files(self, tmp_path):
        (tmp_path / "staging.env").write_text("A=1")
        (tmp_path / "prod.env").write_text("A=2")
        sources = load_from_directory(tmp_path)
        assert "staging.env" in sources
        assert "prod.env" in sources

    def test_non_directory_raises(self, tmp_path):
        f = tmp_path / "file.env"
        f.write_text("A=1")
        with pytest.raises(ValueError):
            load_from_directory(f)

    def test_custom_pattern(self, tmp_path):
        (tmp_path / "config.cfg").write_text("X=1")
        (tmp_path / "other.env").write_text("Y=2")
        sources = load_from_directory(tmp_path, pattern="*.cfg")
        assert "config.cfg" in sources
        assert "other.env" not in sources
