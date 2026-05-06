"""Write audit logs to files or stdout."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional, TextIO

from envdiff.auditor import AuditLog, AuditEvent


def write_audit_json(log: AuditLog, path: str) -> None:
    """Persist the audit log as a JSON file, appending to existing content."""
    dest = Path(path)
    existing_events: list = []

    if dest.exists():
        try:
            data = json.loads(dest.read_text(encoding="utf-8"))
            existing_events = data.get("events", [])
        except (json.JSONDecodeError, OSError):
            existing_events = []

    combined = existing_events + [e.as_dict() for e in log.events]
    dest.write_text(
        json.dumps({"events": combined}, indent=2),
        encoding="utf-8",
    )


def print_audit_event(event: AuditEvent, stream: Optional[TextIO] = None) -> None:
    """Print a human-readable summary of a single audit event."""
    out = stream or sys.stdout
    out.write(f"[{event.timestamp}] {event.left_source} vs {event.right_source}\n")
    out.write(
        f"  added={event.added} removed={event.removed} "
        f"changed={event.changed} unchanged={event.unchanged}\n"
    )
    out.write(f"  redacted={event.redacted}")
    if event.note:
        out.write(f"  note={event.note!r}")
    out.write("\n")


def load_audit_log(path: str) -> AuditLog:
    """Load an AuditLog from a previously written JSON file."""
    from envdiff.auditor import AuditEvent  # local to avoid circular issues

    dest = Path(path)
    if not dest.exists():
        return AuditLog()

    data = json.loads(dest.read_text(encoding="utf-8"))
    events = [
        AuditEvent(
            timestamp=e["timestamp"],
            left_source=e["left_source"],
            right_source=e["right_source"],
            added=e["added"],
            removed=e["removed"],
            changed=e["changed"],
            unchanged=e["unchanged"],
            redacted=e["redacted"],
            note=e.get("note"),
        )
        for e in data.get("events", [])
    ]
    log = AuditLog()
    for ev in events:
        log.record(ev)
    return log
