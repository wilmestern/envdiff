"""Multi-environment comparison matrix.

Compares an arbitrary number of EnvSource objects and builds a matrix
showing the value (or absence) of each key across all environments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.loader import EnvSource
from envdiff.redactor import is_sensitive, redact_value

_MISSING = "<missing>"


@dataclass
class MatrixRow:
    """One row in the comparison matrix (one key, values per env)."""

    key: str
    values: Dict[str, Optional[str]]  # env_name -> value or None
    sensitive: bool = False

    def is_uniform(self) -> bool:
        """Return True when all *present* values are identical."""
        present = [v for v in self.values.values() if v is not None]
        return len(set(present)) <= 1

    def is_complete(self) -> bool:
        """Return True when the key exists in every environment."""
        return all(v is not None for v in self.values.values())

    def as_dict(self) -> dict:
        display = {
            env: (redact_value(v) if self.sensitive and v is not None else v)
            for env, v in self.values.items()
        }
        return {
            "key": self.key,
            "sensitive": self.sensitive,
            "uniform": self.is_uniform(),
            "complete": self.is_complete(),
            "values": display,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"MatrixRow(key={self.key!r}, uniform={self.is_uniform()}, complete={self.is_complete()})"


@dataclass
class DiffMatrix:
    """Full comparison matrix across multiple environments."""

    env_names: List[str]
    rows: List[MatrixRow] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return any(not r.is_uniform() or not r.is_complete() for r in self.rows)

    def uniform_rows(self) -> List[MatrixRow]:
        return [r for r in self.rows if r.is_uniform() and r.is_complete()]

    def differing_rows(self) -> List[MatrixRow]:
        return [r for r in self.rows if not r.is_uniform() or not r.is_complete()]

    def as_dict(self) -> dict:
        return {
            "envs": self.env_names,
            "rows": [r.as_dict() for r in self.rows],
        }


def build_diff_matrix(sources: List[EnvSource], redact: bool = True) -> DiffMatrix:
    """Build a DiffMatrix from a list of EnvSource objects."""
    if not sources:
        return DiffMatrix(env_names=[])

    env_names = [s.name for s in sources]
    all_keys: List[str] = sorted(
        {key for src in sources for key in src.data}
    )

    rows: List[MatrixRow] = []
    for key in all_keys:
        values = {src.name: src.data.get(key) for src in sources}
        sensitive = redact and is_sensitive(key)
        rows.append(MatrixRow(key=key, values=values, sensitive=sensitive))

    return DiffMatrix(env_names=env_names, rows=rows)


def format_matrix_text(matrix: DiffMatrix, show_all: bool = False) -> str:
    """Render the matrix as a human-readable table."""
    rows = matrix.rows if show_all else matrix.differing_rows()
    if not rows:
        return "All keys are identical across environments.\n"

    col_width = max((len(n) for n in matrix.env_names), default=10)
    key_width = max((len(r.key) for r in rows), default=10)

    header = f"{'KEY':<{key_width}}  " + "  ".join(
        f"{n:<{col_width}}" for n in matrix.env_names
    )
    sep = "-" * len(header)
    lines = [header, sep]

    for row in rows:
        d = row.as_dict()
        vals = "  ".join(
            f"{(d['values'].get(n) or _MISSING):<{col_width}}"
            for n in matrix.env_names
        )
        lines.append(f"{row.key:<{key_width}}  {vals}")

    return "\n".join(lines) + "\n"
