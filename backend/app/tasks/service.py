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
    extract: Callable[..., Any] = extract_intent,
) -> list[Task]:
    """Message -> Intent -> Task(s) -> stored. `extract` is injectable so the
    demo/tests can run on canned intents without API calls."""
    intent = extract(message)
    tasks = orchestrate(intent, message, store=store, policy=policy, now=now)
    return repo.add_all(tasks)


def apply_decision(
    repo: TasksRepo,
    task_id: str,
    decision: str,
    *,
    note: str | None = None,
    reviewer: str = "Front desk",
) -> Task | None:
    """approve | dismiss | reopen. Returns the updated task, or None if missing.
    Approval is a status write only — no external action is executed."""
    task = repo.get(task_id)
    if task is None:
        return None
    now = datetime.now(timezone.utc)
    note = note.strip() if note and note.strip() else None

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
    elif decision == "reopen":
        task.status = TaskStatus.needs_action
        task.approved_at = task.rejected_at = task.reviewed_at = task.reviewed_by = None
        task.reviewer_note = None
    else:
        raise ValueError(f"invalid decision: {decision!r}")

    return task
