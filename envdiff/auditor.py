"""Audit trail for environment diff operations."""
from __future__ import annotations

import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from envdiff.differ import DiffResult, DiffStatus


@dataclass
class AuditEvent:
    """A single recorded audit event."""

    timestamp: str
    left_source: str
    right_source: str
    added: int
    removed: int
    changed: int
    unchanged: int
    redacted: bool
    note: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditLog:
    """Collection of audit events."""

    events: List[AuditEvent] = field(default_factory=list)

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)

    def as_dict(self) -> dict:
        return {"events": [e.as_dict() for e in self.events]}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.as_dict(), indent=indent)

    def __len__(self) -> int:
        return len(self.events)


def build_audit_event(
    result: DiffResult,
    left_source: str,
    right_source: str,
    redacted: bool = False,
    note: Optional[str] = None,
) -> AuditEvent:
    """Create an AuditEvent from a DiffResult."""
    counts = {s: 0 for s in DiffStatus}
    for entry in result.entries:
        counts[entry.status] += 1

    return AuditEvent(
        timestamp=datetime.datetime.utcnow().isoformat() + "Z",
        left_source=left_source,
        right_source=right_source,
        added=counts[DiffStatus.ADDED],
        removed=counts[DiffStatus.REMOVED],
        changed=counts[DiffStatus.CHANGED],
        unchanged=counts[DiffStatus.UNCHANGED],
        redacted=redacted,
        note=note,
    )
