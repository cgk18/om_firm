from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field

from .draft import Draft
from .enums import TaskStatus, TaskType
from .intent import ExtractedRequest


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EligibilityCheck(BaseModel):
    """One named, auditable verification step and its outcome. Deterministic by
    design — explainable to a clinic, not a black box."""

    name: str
    passed: bool
    detail: str = ""


class EligibilityResult(BaseModel):
    eligible: bool
    checks: list[EligibilityCheck] = Field(default_factory=list)
    flagged_reason: str | None = None


class Task(BaseModel):
    """A single reviewable unit of work: one patient request → one drafted action,
    queued for a human. Approval marks it `done`; nothing auto-executes.

    `eligibility` and `draft` are present for actionable tasks (refill /
    reschedule) and absent for pure escalations.
    """

    id: str = Field(default_factory=lambda: uuid4().hex)
    message_id: str
    patient_id: str | None = None
    patient_name: str = "Unknown patient"

    type: TaskType
    status: TaskStatus

    request: ExtractedRequest = Field(default_factory=ExtractedRequest)
    agent_summary: str = ""
    eligibility: EligibilityResult | None = None
    draft: Draft | None = None
    flagged_reason: str | None = None

    created_at: datetime = Field(default_factory=_now)
    reviewed_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    reviewed_by: str | None = None
    reviewer_note: str | None = None
