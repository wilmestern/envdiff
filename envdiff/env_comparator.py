"""Side-by-side comparator for two env mappings with alignment and redaction."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envdiff.redactor import redact_value, is_sensitive


@dataclass
class ComparatorRow:
    key: str
    left_value: Optional[str]
    right_value: Optional[str]
    is_sensitive: bool = False
    status: str = "unchanged"  # added | removed | changed | unchanged

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "left": self.left_value,
            "right": self.right_value,
            "sensitive": self.is_sensitive,
            "status": self.status,
        }

    def __repr__(self) -> str:
        return (
            f"ComparatorRow(key={self.key!r}, status={self.status!r}, "
            f"sensitive={self.is_sensitive})"
        )


@dataclass
class ComparisonResult:
    left_name: str
    right_name: str
    rows: List[ComparatorRow] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return any(r.status != "unchanged" for r in self.rows)

    def changed_rows(self) -> List[ComparatorRow]:
        return [r for r in self.rows if r.status != "unchanged"]

    def as_dict(self) -> dict:
        return {
            "left": self.left_name,
            "right": self.right_name,
            "rows": [r.as_dict() for r in self.rows],
        }


def compare_envs(
    left: Dict[str, str],
    right: Dict[str, str],
    left_name: str = "left",
    right_name: str = "right",
    redact: bool = True,
    include_unchanged: bool = True,
) -> ComparisonResult:
    """Compare two env dicts and return a ComparisonResult with aligned rows."""
    all_keys = sorted(set(left) | set(right))
    rows: List[ComparatorRow] = []

    for key in all_keys:
        sensitive = is_sensitive(key)
        lv = left.get(key)
        rv = right.get(key)

        if redact and sensitive:
            display_lv = redact_value(lv) if lv is not None else None
            display_rv = redact_value(rv) if rv is not None else None
        else:
            display_lv, display_rv = lv, rv

        if lv is None:
            status = "added"
        elif rv is None:
            status = "removed"
        elif lv != rv:
            status = "changed"
        else:
            status = "unchanged"

        if not include_unchanged and status == "unchanged":
            continue

        rows.append(
            ComparatorRow(
                key=key,
                left_value=display_lv,
                right_value=display_rv,
                is_sensitive=sensitive,
                status=status,
            )
        )

    return ComparisonResult(left_name=left_name, right_name=right_name, rows=rows)


def format_comparison_text(
    result: ComparisonResult,
    col_width: int = 40,
) -> str:
    """Render a ComparisonResult as a human-readable side-by-side table."""
    STATUS_SYMBOLS = {
        "added": "+",
        "removed": "-",
        "changed": "~",
        "unchanged": " ",
    }
    header_left = result.left_name[:col_width].ljust(col_width)
    header_right = result.right_name[:col_width].ljust(col_width)
    sep = "-" * (col_width * 2 + 20)
    lines = [
        f"  {'KEY':<30} {header_left} {header_right}",
        sep,
    ]
    for row in result.rows:
        sym = STATUS_SYMBOLS.get(row.status, " ")
        lv = (row.left_value or "")[:col_width].ljust(col_width)
        rv = (row.right_value or "")[:col_width].ljust(col_width)
        lines.append(f"{sym} {row.key:<30} {lv} {rv}")
    return "\n".join(lines)
