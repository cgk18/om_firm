from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class Provider(BaseModel):
    id: str
    name: str
    working_hours: dict[str, list[str]] | None = None 
    covering_provider_id: str | None = None


class Prescription(BaseModel):
    """A seeded prescription record. Eligibility reads these to verify a refill
    (active? dosage doctor-approved? controlled? conflicts?). Read-only.

    `prescribed_date` is the original start date — used to measure how long two
    conflicting meds have overlapped (an established >1yr overlap is tolerated).
    """

    id: str
    patient_id: str
    provider_id: str
    medication_name: str
    dosage: str
    instructions: str = ""
    active: bool = True
    prescribed_date: date | None = None
    last_filled: date | None = None
    days_supply: int = 30  # days a fill lasts — used to spot a too-early refill
    valid_until: date | None = None  # script expiration; None = unknown/skip the check
    controlled: bool = False


class ApprovedMed(BaseModel):
    """A medication+dosage the provider approved at a visit — the structured,
    auditable form of "it's in the doctor's notes." Lets the refill check accept
    a dosage that matches the visit's approval even if it differs from the script."""

    medication_name: str
    dosage: str


class Appointment(BaseModel):
    """A seeded appointment. Used for last-visit lookup, reschedule conflict
    checks, and the doctor-approved-dosage source. Read-only."""

    id: str
    patient_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    status: str = "scheduled"  # scheduled | completed | cancelled
    times_rescheduled: int = 0  # how many times this appointment has already been moved
    notes: str | None = None  # free-text provider notes (shown on the card)
    approved_meds: list[ApprovedMed] = Field(default_factory=list)  # structured dosage approvals


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
    status: str = "active"  # active | inactive | discharged | deceased | transferred
    primary_provider_id: str | None = None  # the patient's usual provider

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
