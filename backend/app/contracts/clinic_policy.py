from __future__ import annotations

from pydantic import BaseModel, Field


class ClinicPolicy(BaseModel):
    """Per-clinic eligibility configuration (Level 1: parameterize fixed rules).

    Every eligibility check reads its thresholds / lists / toggles from here
    instead of hardcoded constants. Ship `default_policy()`; clients tweak the
    values. This is NOT a general rules engine — clients change knobs, not author
    new rule types (that's Level 2, deferred).

    Default values reflect the refill ruleset agreed for v1 (visit recency vs.
    planned-visit window, established-conflict threshold). Tune the values here;
    the rule *set* lives in eligibility/.
    """

    # --- Refill rules ---
    # Visit requirement passes if EITHER: a visit within the last
    # `refill_recent_visit_days`, OR a future appointment scheduled within the
    # next `refill_future_visit_window_days`.
    refill_recent_visit_days: int = 122  # ~4 months (a third of a year)
    refill_future_visit_window_days: int = 365  # a planned visit within the next year
    # A drug conflict is "established"/tolerated once the two meds have overlapped
    # for at least this long; a fresher conflict routes to the provider.
    conflict_established_days: int = 365
    controlled_substance_excluded: bool = True  # controlled meds always escalate

    # --- Insurance (checked against the patient's on-file plan, not the call) ---
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
