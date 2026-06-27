"""API request/response models — the contract the dashboard codes against.

`TaskView` is the enriched task: the `Task` plus the transcript (from its Message)
and the read-only patient-context card, joined so the UI needs one call per screen.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.contracts import Task


class MedView(BaseModel):
    medication_name: str
    dosage: str
    instructions: str


class ApptView(BaseModel):
    start_time: datetime
    provider_name: str | None
    status: str


class PatientCard(BaseModel):
    """Read-only context card from seeded data — what the reviewer approves against."""

    id: str
    full_name: str
    date_of_birth: date
    phone: str | None
    insurance_plan: str | None
    last_visit: date | None
    status: str
    primary_provider: str | None
    active_medications: list[MedView]
    upcoming_appointments: list[ApptView]


class TaskView(BaseModel):
    task: Task
    transcript: str | None = None
    patient: PatientCard | None = None


class DecisionRequest(BaseModel):
    decision: str  # approve | dismiss | edit | reopen
    note: str | None = None
    edited_text: str | None = None  # for decision == "edit"
    reviewer: str = "Front desk"


class IngestRequest(BaseModel):
    transcript: str
    channel: str = "voicemail"  # voicemail | email
