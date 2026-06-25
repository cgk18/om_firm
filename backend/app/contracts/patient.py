from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class Provider(BaseModel):
    id: str
    name: str


class Prescription(BaseModel):
    """A seeded prescription record. Eligibility reads these to verify a refill
    (active? dosage match? controlled?). Read-only — never written back."""

    id: str
    patient_id: str
    provider_id: str
    medication_name: str
    dosage: str
    instructions: str = ""
    active: bool = True
    last_filled: date | None = None
    controlled: bool = False


class Appointment(BaseModel):
    """A seeded appointment. Used for last-visit lookup and reschedule conflict
    checks. Read-only."""

    id: str
    patient_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    status: str = "scheduled"  # scheduled | completed | cancelled


class Patient(BaseModel):
    """Seeded read-only "EHR" record. Simulates the chart for eligibility checks
    and the dashboard context card. Never written back to.

    Active meds and appointments live as separate `Prescription` / `Appointment`
    records keyed by `patient_id` in the seed store, not embedded here.
    """

    id: str
    first_name: str
    last_name: str
    date_of_birth: date
    phone: str | None = None
    insurance_plan: str | None = None
    last_visit: date | None = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
