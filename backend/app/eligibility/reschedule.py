"""Reschedule eligibility + slot-finding — deterministic, policy-driven, auditable.

Reads the chart through `store`; only READS holds (the orchestrator reserves once
a task id exists). Rules: default hours 08:30–17:00 Mon–Fri (Provider.working_hours
overrides); holidays from store.holidays; duration = appointment_duration_minutes;
requested slot taken -> propose nearest + flag; primary full -> covering provider;
slot > reschedule_far_out_days out -> "far out" flag; window = reschedule_search_days.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

from app.contracts import (
    Appointment,
    ClinicPolicy,
    EligibilityCheck,
    EligibilityResult,
    ExtractedRequest,
    Patient,
)

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
_TIME_OF_DAY_HOUR = {"morning": 9, "afternoon": 13, "evening": 16}
_STEP_MINUTES = 15


@dataclass
class RescheduleAssessment:
    eligibility: EligibilityResult
    proposed_start: datetime | None = None
    proposed_end: datetime | None = None
    provider_id: str | None = None
    cancel_appointment_id: str | None = None
    requested_was_available: bool = False
    switched_provider: bool = False
    far_out: bool = False
    is_new_booking: bool = False
    repeated_reschedule: bool = False  # appointment moved >= threshold times already


def resolve_requested_window(request: ExtractedRequest, policy: ClinicPolicy) -> tuple[datetime, datetime] | None:
    """preferred_times[0] -> (start, end). None if no day was given."""
    pts = request.preferred_times
    if not pts or pts[0].date is None:
        return None
    pt = pts[0]
    if pt.start_time:
        hour, minute = (int(x) for x in pt.start_time.split(":"))
    else:
        hour, minute = _TIME_OF_DAY_HOUR.get(pt.time_of_day.value, 9), 0
    start = datetime.combine(pt.date, time(hour, minute), tzinfo=timezone.utc)
    return start, start + timedelta(minutes=policy.appointment_duration_minutes)


def slot_is_available(
    start: datetime,
    end: datetime,
    provider_id: str,
    *,
    store,
    holds,
    policy: ClinicPolicy,
    exclude_appointment_id: str | None = None,
) -> bool:
    # holiday
    if start.date().isoformat() in store.holidays:
        return False
    # provider working hours for that weekday
    hours = store.working_hours_for(provider_id, policy)
    key = WEEKDAY_KEYS[start.weekday()]
    if key not in hours:
        return False  # closed that day (e.g. weekend)
    work_start = _at(start, hours[key][0])
    work_end = _at(start, hours[key][1])
    if start < work_start or end > work_end:
        return False
    # overlap with a booked appointment
    for a in store.scheduled_for_provider(provider_id):
        if a.id == exclude_appointment_id:
            continue
        if start < a.end_time and end > a.start_time:
            return False
    # overlap with an active hold
    if holds.conflicts(provider_id, start, end):
        return False
    return True


def find_next_available(
    start: datetime,
    provider_id: str,
    *,
    store,
    holds,
    policy: ClinicPolicy,
    exclude_appointment_id: str | None = None,
) -> tuple[datetime, datetime] | None:
    """Soonest available slot at or after `start`, within reschedule_search_days."""
    duration = timedelta(minutes=policy.appointment_duration_minutes)
    midnight = start.replace(hour=0, minute=0, second=0, microsecond=0)
    for day_offset in range(policy.reschedule_search_days):
        day = midnight + timedelta(days=day_offset)
        for minutes in range(0, 24 * 60, _STEP_MINUTES):
            cand_start = day + timedelta(minutes=minutes)
            if cand_start < start:
                continue
            cand_end = cand_start + duration
            if slot_is_available(
                cand_start, cand_end, provider_id,
                store=store, holds=holds, policy=policy,
                exclude_appointment_id=exclude_appointment_id,
            ):
                return cand_start, cand_end
    return None


def appointment_to_move(patient: Patient, *, store, now: datetime) -> Appointment | None:
    """Patient's soonest upcoming appointment, or None (-> new booking)."""
    upcoming = store.future_appointments(patient.id, now=now)
    return min(upcoming, default=None, key=lambda a: a.start_time)


def assess_reschedule(
    *,
    request: ExtractedRequest,
    patient: Patient,
    store,
    holds,
    policy: ClinicPolicy,
    now: datetime,
) -> RescheduleAssessment:
    moving = appointment_to_move(patient, store=store, now=now)
    is_new_booking = moving is None
    exclude_id = moving.id if moving else None
    repeated = bool(moving) and moving.times_rescheduled >= policy.reschedule_repeat_flag_threshold

    if moving:
        provider_id = moving.provider_id
    else:
        # New booking: infer the provider from their most recent completed visit.
        last = store.last_completed_appointment(patient.id, now=now)
        provider_id = last.provider_id if last else None

    if provider_id is None:
        return _not_eligible("select_provider", "No appointment or prior provider on file — select a provider manually.", is_new_booking=is_new_booking)

    window = resolve_requested_window(request, policy)
    switched_provider = False

    if window and slot_is_available(*window, provider_id, store=store, holds=holds, policy=policy, exclude_appointment_id=exclude_id):
        proposed = window
        requested_was_available = True
    else:
        requested_was_available = False
        search_from = window[0] if window else now
        proposed = find_next_available(search_from, provider_id, store=store, holds=holds, policy=policy, exclude_appointment_id=exclude_id)
        if proposed is None:
            cover = store.provider(provider_id).covering_provider_id if store.provider(provider_id) else None
            if cover:
                proposed = find_next_available(search_from, cover, store=store, holds=holds, policy=policy)
                if proposed:
                    switched_provider = True
                    provider_id = cover

    if proposed is None:
        return _not_eligible("no_slot_available", f"No open slot within {policy.reschedule_search_days} days.", is_new_booking=is_new_booking)

    far_out = (proposed[0].date() - now.date()).days > policy.reschedule_far_out_days

    checks = [
        EligibilityCheck(name="slot_found", passed=True, detail=f"Proposed {proposed[0]:%a %b %d %H:%M}."),
        EligibilityCheck(name="requested_time_available", passed=requested_was_available,
                         detail="Requested time is open." if requested_was_available else "Requested time was taken — proposed the nearest slot."),
        EligibilityCheck(name="primary_provider_available", passed=not switched_provider,
                         detail="Original provider available." if not switched_provider else "Original provider full — using covering provider."),
        EligibilityCheck(name="within_window", passed=not far_out,
                         detail="Within a month." if not far_out else "More than a month out."),
        EligibilityCheck(name="reschedule_frequency", passed=not repeated,
                         detail=(f"This appointment has already been rescheduled {moving.times_rescheduled} times — review for over-rescheduling."
                                 if repeated else "Reschedule frequency is normal.")),
    ]
    flagged = "; ".join(c.detail for c in checks if not c.passed) or None

    return RescheduleAssessment(
        eligibility=EligibilityResult(eligible=True, checks=checks, flagged_reason=flagged),
        proposed_start=proposed[0],
        proposed_end=proposed[1],
        provider_id=provider_id,
        cancel_appointment_id=exclude_id,
        requested_was_available=requested_was_available,
        switched_provider=switched_provider,
        far_out=far_out,
        is_new_booking=is_new_booking,
        repeated_reschedule=repeated,
    )


# ----------------------------------------------------------------- helpers ----
def _at(day: datetime, hhmm: str) -> datetime:
    hour, minute = (int(x) for x in hhmm.split(":"))
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _not_eligible(code: str, detail: str, *, is_new_booking: bool) -> RescheduleAssessment:
    return RescheduleAssessment(
        eligibility=EligibilityResult(
            eligible=False,
            checks=[EligibilityCheck(name=code, passed=False, detail=detail)],
            flagged_reason=detail,
        ),
        is_new_booking=is_new_booking,
    )
