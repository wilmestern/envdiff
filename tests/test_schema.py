"""Tests for envdiff.schema module."""

import json
import pytest
from pathlib import Path
from envdiff.schema import EnvSchema, load_schema_from_dict, load_schema_from_file


class TestEnvSchema:
    def test_defaults(self):
        schema = EnvSchema()
        assert schema.required == []
        assert schema.warn_empty is False
        assert schema.error_empty is False

    def test_repr_contains_required(self):
        schema = EnvSchema(required=["FOO"])
        assert "FOO" in repr(schema)


class TestLoadSchemaFromDict:
    def test_loads_required_keys(self):
        schema = load_schema_from_dict({"required": ["DB_URL", "SECRET_KEY"]})
        assert "DB_URL" in schema.required
        assert "SECRET_KEY" in schema.required

    def test_loads_warn_empty(self):
        schema = load_schema_from_dict({"warn_empty": True})
        assert schema.warn_empty is True

    def test_loads_error_empty(self):
        schema = load_schema_from_dict({"error_empty": True})
        assert schema.error_empty is True

    def test_empty_dict_gives_defaults(self):
        schema = load_schema_from_dict({})
        assert schema.required == []
        assert schema.warn_empty is False

    def test_unknown_key_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown schema keys"):
            load_schema_from_dict({"unknown_field": True})


class TestLoadSchemaFromFile:
    def test_loads_json_file(self, tmp_path: Path):
        data = {"required": ["HOST", "PORT"], "warn_empty": True}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(data), encoding="utf-8")

        schema = load_schema_from_file(schema_file)
        assert "HOST" in schema.required
        assert "PORT" in schema.required
        assert schema.warn_empty is True

    def test_unsupported_extension_raises(self, tmp_path: Path):
        bad_file = tmp_path / "schema.toml"
        bad_file.write_text("[schema]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Unsupported schema file format"):
            load_schema_from_file(bad_file)

    def test_missing_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_schema_from_file(tmp_path / "nonexistent.json")

    def test_json_with_error_empty(self, tmp_path: Path):
        data = {"error_empty": True}
        schema_file = tmp_path / "schema.json"
        schema_file.write_text(json.dumps(data), encoding="utf-8")
        schema = load_schema_from_file(schema_file)
        assert schema.error_empty is True
        assert schema.warn_empty is False
