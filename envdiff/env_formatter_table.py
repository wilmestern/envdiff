"""Table formatter for environment variable comparisons."""
from __future__ import annotations

from typing import Dict, List, Optional


class TableRow:
    """A single row in a formatted environment table."""

    def __init__(self, key: str, value: str, source: str, sensitive: bool = False) -> None:
        self.key = key
        self.value = value
        self.source = source
        self.sensitive = sensitive

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "sensitive": self.sensitive,
        }

    def __repr__(self) -> str:
        return f"TableRow(key={self.key!r}, source={self.source!r})"


def build_table(envs: Dict[str, Dict[str, str]], redact: bool = True) -> List[TableRow]:
    """Build a flat list of TableRow objects from multiple env mappings.

    Args:
        envs: Mapping of source name -> env dict.
        redact: If True, sensitive values are replaced with '***'.

    Returns:
        Sorted list of TableRow instances.
    """
    from envdiff.redactor import is_sensitive, redact_value

    rows: List[TableRow] = []
    for source, mapping in envs.items():
        for key, value in mapping.items():
            sensitive = is_sensitive(key)
            display_value = redact_value(key, value) if (redact and sensitive) else value
            rows.append(TableRow(key=key, value=display_value, source=source, sensitive=sensitive))
    rows.sort(key=lambda r: (r.key, r.source))
    return rows


def format_table_text(
    rows: List[TableRow],
    col_widths: Optional[Dict[str, int]] = None,
) -> str:
    """Render TableRow list as a plain-text aligned table.

    Args:
        rows: Rows produced by build_table.
        col_widths: Optional override for column widths.

    Returns:
        Multi-line string with header and data rows.
    """
    if not rows:
        return "(no entries)"

    key_w = max(len(r.key) for r in rows)
    src_w = max(len(r.source) for r in rows)
    val_w = max(len(r.value) for r in rows)

    if col_widths:
        key_w = col_widths.get("key", key_w)
        src_w = col_widths.get("source", src_w)
        val_w = col_widths.get("value", val_w)

    header = f"{'KEY':<{key_w}}  {'SOURCE':<{src_w}}  {'VALUE':<{val_w}}"
    separator = "-" * len(header)
    lines = [header, separator]
    for row in rows:
        lines.append(f"{row.key:<{key_w}}  {row.source:<{src_w}}  {row.value:<{val_w}}")
    return "\n".join(lines)
