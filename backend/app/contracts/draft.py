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


# Discriminated on `type` so a Draft round-trips to/from JSON as the right action.
DraftAction = Annotated[
    Union[RefillAction, RescheduleAction], Field(discriminator="type")
]


class Draft(BaseModel):
    """The heart of the draft-and-route pivot.

    Carries two halves:
      - `structured` — a machine-pushable action (Tier-2-ready: one-click push
        once an EHR is integrated).
      - `rendered`   — human-readable text the CHW reads / edits / copies into
        their own system today (Tier-1-useful with no integration).

    NEVER auto-executed. Approval marks the task done; a human acts on it.
    """

    structured: DraftAction
    rendered: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    editable: bool = True
