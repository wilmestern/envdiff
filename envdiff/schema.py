"""Schema loader: reads a YAML/JSON schema file defining required keys and rules."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


_VALID_TOP_KEYS = {"required", "warn_empty", "error_empty"}


@dataclass_like = None  # placeholder — we use a plain class below


class EnvSchema:
    """Represents validation rules loaded from a schema file."""

    def __init__(
        self,
        required: Optional[List[str]] = None,
        warn_empty: bool = False,
        error_empty: bool = False,
    ) -> None:
        self.required: List[str] = required or []
        self.warn_empty: bool = warn_empty
        self.error_empty: bool = error_empty

    def __repr__(self) -> str:
        return (
            f"EnvSchema(required={self.required!r}, "
            f"warn_empty={self.warn_empty}, error_empty={self.error_empty})"
        )


def _parse_schema_dict(data: Dict[str, Any]) -> EnvSchema:
    unknown = set(data.keys()) - _VALID_TOP_KEYS
    if unknown:
        raise ValueError(f"Unknown schema keys: {sorted(unknown)}")
    return EnvSchema(
        required=data.get("required", []),
        warn_empty=bool(data.get("warn_empty", False)),
        error_empty=bool(data.get("error_empty", False)),
    )


def load_schema_from_dict(data: Dict[str, Any]) -> EnvSchema:
    """Build an EnvSchema from a plain dictionary."""
    return _parse_schema_dict(data)


def load_schema_from_file(path: str | Path) -> EnvSchema:
    """Load an EnvSchema from a JSON or YAML file."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()

    if suffix == ".json":
        data = json.loads(text)
    elif suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise ImportError("PyYAML is required to load YAML schema files. pip install pyyaml")
        data = yaml.safe_load(text)
    else:
        raise ValueError(f"Unsupported schema file format: {suffix!r}. Use .json or .yaml/.yml")

    return _parse_schema_dict(data)
