"""Slot holds (reservations) — in-memory, session-lived (like tasks/repo.py).

A hold is a soft lock on a (provider, start, end) window tied to the task that
proposed it, so a second patient can't be proposed into the same slot. It is NOT
a booking — booking happens in the clinic's own system after a human approves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Hold:
    provider_id: str
    start: datetime
    end: datetime
    task_id: str
    created_at: datetime = field(default_factory=_now)
    expires_at: datetime | None = None  # None = no expiry; release() frees it


class HoldStore:
    def __init__(self) -> None:
        self._holds: dict[str, Hold] = {}  # keyed by task_id

    def reserve(self, provider_id: str, start: datetime, end: datetime, task_id: str) -> Hold:
        """Reserve the window for a task, replacing any prior hold for that task
        (re-running intake on the same message must not stack holds)."""
        hold = Hold(provider_id=provider_id, start=start, end=end, task_id=task_id)
        self._holds[task_id] = hold
        return hold

    def release(self, task_id: str) -> None:
        self._holds.pop(task_id, None)

    def conflicts(self, provider_id: str, start: datetime, end: datetime, *, exclude_task_id: str | None = None) -> bool:
        """True if an active hold for this provider overlaps [start, end)."""
        for h in self._holds.values():
            if h.provider_id != provider_id:
                continue
            if exclude_task_id is not None and h.task_id == exclude_task_id:
                continue
            if start < h.end and end > h.start:  # half-open overlap; back-to-back is fine
                return True
        return False

    def list(self) -> list[Hold]:
        return list(self._holds.values())
