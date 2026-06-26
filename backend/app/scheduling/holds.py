"""Slot holds (reservations) — in-memory, session-lived (like tasks/repo.py).

A hold is a soft lock on a (provider, start, end) window tied to the task that
proposed it, so a second patient can't be proposed into the same slot. It is NOT
a booking — booking happens in the clinic's own system after a human approves.
Build this first (it depends on nothing) and unit-test it standalone.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Hold:
    provider_id: str
    start: datetime
    end: datetime
    task_id: str
    # TODO (optional stretch): created_at: datetime / expires_at: datetime for auto-expiry.
    #   For the demo you can skip expiry and just release() on dismiss/reopen.


class HoldStore:
    def __init__(self) -> None:
        # TODO: hold storage, e.g. self._holds: dict[str, Hold] = {}  (keyed by task_id)
        raise NotImplementedError

    def reserve(self, provider_id: str, start: datetime, end: datetime, task_id: str) -> Hold:
        # TODO: build a Hold and store it, REPLACING any existing hold for this task_id
        #       (re-running intake on the same message must not stack holds). Return it.
        raise NotImplementedError

    def release(self, task_id: str) -> None:
        # TODO: drop the hold(s) for this task_id (no error if none exist).
        raise NotImplementedError

    def conflicts(self, provider_id: str, start: datetime, end: datetime, *, exclude_task_id: str | None = None) -> bool:
        # TODO: True if any active hold for THIS provider overlaps [start, end):
        #         same provider_id AND start < hold.end AND end > hold.start
        #       Skip the hold whose task_id == exclude_task_id (a task shouldn't
        #       conflict with its own previously-proposed slot).
        raise NotImplementedError

    def list(self) -> list[Hold]:
        # TODO: return all active holds (handy for the dashboard / debugging).
        raise NotImplementedError
