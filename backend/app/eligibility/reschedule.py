"""Reschedule eligibility + slot-finding.   ★ YOUR HOMEWORK ★

Mirrors eligibility/refill.py: deterministic, policy-driven, auditable, reading
the chart through `store`. Difference: it also FINDS a slot, so the result
carries a proposed time. Build bottom-up in the order the functions appear here;
each has its TODOs inline. Keep these pure — do NOT reserve holds here (the
orchestrator does that once a task id exists); these only READ holds.

Rules recap: default hours 08:30–17:00 Mon–Fri (Provider.working_hours overrides);
holidays from store.holidays; duration = policy.appointment_duration_minutes;
requested slot taken -> propose nearest + flag; primary full -> covering provider;
slot > policy.reschedule_far_out_days out -> "far out" flag; search window =
policy.reschedule_search_days.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.contracts import (
    Appointment,
    ClinicPolicy,
    EligibilityCheck,
    EligibilityResult,
    ExtractedRequest,
    Patient,
)

WEEKDAY_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


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


def resolve_requested_window(request: ExtractedRequest, policy: ClinicPolicy) -> tuple[datetime, datetime] | None:
    # TODO: take request.preferred_times[0]; if there are none -> return None.
    # TODO: build `start` from its .date plus a time:
    #         - if .start_time ("HH:MM") set -> use it
    #         - elif .time_of_day -> morning 09:00 / afternoon 13:00 / evening 16:00 / else 09:00
    #       make it tz-aware: datetime(y, m, d, hh, mm, tzinfo=timezone.utc)
    # TODO: end = start + timedelta(minutes=policy.appointment_duration_minutes)
    # TODO: return (start, end)
    raise NotImplementedError


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
    # TODO: holiday  -> if start.date().isoformat() in store.holidays: return False
    # TODO: hours    -> hours = store.working_hours_for(provider_id, policy)
    #                   key = WEEKDAY_KEYS[start.weekday()]; if key not in hours: return False (closed)
    #                   work_start/work_end = that date at hours[key][0] / [1]
    #                   if start < work_start or end > work_end: return False
    # TODO: booked   -> for a in store.scheduled_for_provider(provider_id):
    #                       if a.id == exclude_appointment_id: continue
    #                       if start < a.end_time and end > a.start_time: return False  (overlap)
    # TODO: held     -> if holds.conflicts(provider_id, start, end): return False
    # TODO: return True
    raise NotImplementedError


def find_next_available(
    start: datetime,
    provider_id: str,
    *,
    store,
    holds,
    policy: ClinicPolicy,
    exclude_appointment_id: str | None = None,
) -> tuple[datetime, datetime] | None:
    # TODO: duration = timedelta(minutes=policy.appointment_duration_minutes)
    # TODO: step forward from `start` in 15-min increments, up to
    #       policy.reschedule_search_days days. For each candidate_start:
    #         candidate_end = candidate_start + duration
    #         if slot_is_available(candidate_start, candidate_end, provider_id, store=store,
    #                              holds=holds, policy=policy, exclude_appointment_id=exclude_appointment_id):
    #             return (candidate_start, candidate_end)
    # TODO: nothing found in the window -> return None
    # Hint: let slot_is_available reject holidays/off-hours/overlaps; you just sweep times.
    raise NotImplementedError


def appointment_to_move(patient: Patient, *, store, now: datetime) -> Appointment | None:
    # TODO: upcoming = store.future_appointments(patient.id, now=now)
    # TODO: return the earliest by .start_time, or None (None -> it's a new booking).
    raise NotImplementedError


def assess_reschedule(
    *,
    request: ExtractedRequest,
    patient: Patient,
    store,
    holds,
    policy: ClinicPolicy,
    now: datetime,
) -> RescheduleAssessment:
    checks: list[EligibilityCheck] = []

    # TODO 1 (which appt / which provider):
    #   moving = appointment_to_move(patient, store=store, now=now)
    #   is_new_booking = moving is None
    #   provider_id = moving.provider_id if moving else <new-booking provider — you decided to
    #                 flag for manual selection; pick how you represent that>
    #   exclude_id = moving.id if moving else None

    # TODO 2 (requested window):
    #   window = resolve_requested_window(request, policy)
    #   if window is None: no time requested -> propose soonest via find_next_available(now, ...) and
    #                      record a check noting "no time requested".

    # TODO 3 (find the slot):
    #   if window and slot_is_available(*window, provider_id, store=store, holds=holds,
    #                                   policy=policy, exclude_appointment_id=exclude_id):
    #       proposed = window; requested_was_available = True
    #   else:
    #       requested_was_available = False
    #       proposed = find_next_available(window[0] if window else now, provider_id, ...)
    #       if proposed is None:                       # primary full -> try covering
    #           cov = store.provider(provider_id).covering_provider_id if provider_id else None
    #           if cov:
    #               proposed = find_next_available(window[0] if window else now, cov, ...)
    #               if proposed: switched_provider = True; provider_id = cov

    # TODO 4 (no slot anywhere):
    #   if proposed is None -> append a failing EligibilityCheck("slot_found", False, ...) and
    #   return a not-eligible RescheduleAssessment (no proposed_start). Stop here.

    # TODO 5 (flags + checks):
    #   far_out = (proposed[0].date() - now.date()).days > policy.reschedule_far_out_days
    #   append named checks (requested_time_available, slot_found, within_window) so the dashboard
    #   shows the same audit list refills get. eligible = all(c.passed for c in checks).

    # TODO 6 (return):
    #   return RescheduleAssessment(
    #       eligibility=EligibilityResult(eligible=..., checks=checks, flagged_reason=...),
    #       proposed_start=proposed[0], proposed_end=proposed[1], provider_id=provider_id,
    #       cancel_appointment_id=moving.id if moving else None,
    #       requested_was_available=..., switched_provider=..., far_out=far_out, is_new_booking=is_new_booking)
    raise NotImplementedError
