from __future__ import annotations

from pydantic import BaseModel, Field


class ClinicPolicy(BaseModel):
    """Per-clinic eligibility configuration (Level 1: parameterize fixed rules).

    Every eligibility check reads its thresholds / lists / toggles from here
    instead of hardcoded constants. Ship `default_policy()`; clients tweak the
    values. This is NOT a general rules engine — clients change knobs, not author
    new rule types (that's Level 2, deferred).

    NOTE: the default *values* below are carried from the hackathon and are up
    for review (see ARCHITECTURE.md TODO) — change the defaults, not the shape.
    """

    # --- Refill rules ---
    refill_visit_window_days: int = 183  # last visit must fall within this window
    require_dosage_match: bool = True  # requested dosage must match the active script
    controlled_substance_excluded: bool = True  # controlled meds always escalate

    # --- Insurance ---
    accepted_insurance: list[str] = Field(default_factory=list)  # empty list = accept all

    # --- Reschedule rules ---
    reschedule_max_lead_days: int = 60  # how far out a proposed slot may be
    appointment_duration_minutes: int = 30


def default_policy() -> ClinicPolicy:
    """The policy the demo ships with. Clients change these values, not the rules."""
    return ClinicPolicy(
        accepted_insurance=[
            "Aetna",
            "Blue Cross Blue Shield",
            "UnitedHealthcare",
            "Cigna",
            "Medicare",
        ],
    )
