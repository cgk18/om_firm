from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class RefillAction(BaseModel):
    """Structured refill payload — exactly what a future Tier-2 EHR push would
    send. Today it backs the rendered draft; it is never executed."""

    type: Literal["refill"] = "refill"
    patient_id: str
    medication: str
    dosage: str
    instructions: str = ""
    provider_id: str | None = None


class RescheduleAction(BaseModel):
    """Structured reschedule payload — a *proposed* slot, not a booking."""

    type: Literal["reschedule"] = "reschedule"
    patient_id: str
    provider_id: str | None = None
    new_start: datetime
    new_end: datetime
    cancel_appointment_id: str | None = None


class MessageRelayAction(BaseModel):
    """Structured relay payload — a drafted note to forward to the provider.
    `message` is the body staff review (and may edit) before sending."""

    type: Literal["message_relay"] = "message_relay"
    patient_id: str
    provider_id: str | None = None
    message: str


# Discriminated on `type` so a Draft round-trips to/from JSON as the right action.
DraftAction = Annotated[
    Union[RefillAction, RescheduleAction, MessageRelayAction], Field(discriminator="type")
]


class Blocker(BaseModel):
    """A prerequisite that must be cleared before a task can be resolved — usually
    a failed eligibility check re-expressed as an imperative next step, but also
    task-level needs with no draft (e.g. "verify the patient's identity").

    Lives on the `Task` (not the `Draft`), so a task carries its action items
    whether or not it has a drafted action. `code` is the machine handle the
    dashboard can wire an action to; `label` is the imperative shown to staff;
    `detail` is the why.
    """

    code: str  # e.g. "schedule_visit" | "dosage_mismatch" | "no_patient_match" | "verify_identity"
    label: str
    detail: str = ""


class Draft(BaseModel):
    """The heart of the draft-and-route pivot.

    Carries two halves:
      - `structured` — a machine-pushable action (Tier-2-ready: one-click push
        once an EHR is integrated).
      - `rendered`   — human-readable text the CHW reads / edits / copies into
        their own system today (Tier-1-useful with no integration).

    NEVER auto-executed. Approval marks the task approved; a human acts on it.
    Action-needed items live on the Task (`Task.blockers`), not here.
    """

    structured: DraftAction
    rendered: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    editable: bool = True
