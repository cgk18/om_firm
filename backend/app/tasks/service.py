"""Task service — create tasks from a message, and apply a human decision.

Draft-and-route: approving a task marks it `approved`; it does NOT execute
anything. The human carries the draft into their own system. Nothing here calls
an EHR, sends an SMS, or books an appointment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from app.contracts import Message, Task, TaskStatus
from app.pipeline.intake import extract_intent
from app.pipeline.orchestrator import orchestrate

from .repo import TasksRepo


def intake_to_tasks(
    message: Message,
    *,
    repo: TasksRepo,
    store,
    policy,
    now: datetime,
    holds=None,
    extract: Callable[..., Any] = extract_intent,
) -> list[Task]:
    """Message -> Intent -> Task(s) -> stored. `extract` is injectable so the
    demo/tests can run on canned intents without API calls. `holds` is the slot
    reservation store (orchestrator uses a no-op one if omitted)."""
    intent = extract(message)
    tasks = orchestrate(intent, message, store=store, policy=policy, now=now, holds=holds)
    return repo.add_all(tasks)


def apply_decision(
    repo: TasksRepo,
    task_id: str,
    decision: str,
    *,
    note: str | None = None,
    reviewer: str = "Front desk",
    edited_text: str | None = None,
    holds=None,
) -> Task | None:
    """approve | dismiss | reopen | edit. Returns the updated task, or None if
    missing. Approval is a status write only — no external action is executed.
    `edit` replaces the draft's rendered text (and a relay's message body) with
    the staff-edited version; status is unchanged so they can then approve."""
    task = repo.get(task_id)
    if task is None:
        return None
    now = datetime.now(timezone.utc)
    note = note.strip() if note and note.strip() else None

    if decision == "edit":
        if task.draft is not None and edited_text is not None:
            task.draft.rendered = edited_text
            if getattr(task.draft.structured, "type", None) == "message_relay":
                task.draft.structured.message = edited_text
        if note:
            task.reviewer_note = note
        return task

    if decision == "approve":
        task.status = TaskStatus.approved
        task.approved_at = now
        task.reviewed_at = now
        task.reviewed_by = reviewer
        task.reviewer_note = note
    elif decision == "dismiss":
        task.status = TaskStatus.dismissed
        task.rejected_at = now
        task.reviewed_at = now
        task.reviewed_by = reviewer
        task.reviewer_note = note
        if holds is not None:  # free any slot a rejected reschedule was holding
            holds.release(task_id)
    elif decision == "reopen":
        task.status = TaskStatus.needs_action
        task.approved_at = task.rejected_at = task.reviewed_at = task.reviewed_by = None
        task.reviewer_note = None
    else:
        raise ValueError(f"invalid decision: {decision!r}")

    return task
