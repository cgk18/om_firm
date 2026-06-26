"""Refill eligibility — deterministic, policy-driven, auditable.

Implements the v1 refill ruleset:
  1. active prescription on file for the requested med
  2. dosage approved by the provider (active script OR last-visit notes); a dose
     the caller did not state defaults to the script and passes
  3. visit requirement: a visit within the last `refill_recent_visit_days` OR a
     scheduled visit within the next `refill_future_visit_window_days`
  4. not a controlled substance
  5. insurance accepted (the patient's ON-FILE plan, not what they said on the call)
  6. no unestablished drug conflict (a conflict tolerated once the two meds have
     overlapped >= `conflict_established_days`)

Reads the chart through the store (our read-only "EHR" interface); swapping in a
real EHR later means swapping the store, not this logic.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.contracts import (
    ClinicPolicy,
    EligibilityCheck,
    EligibilityResult,
    ExtractedRequest,
    Patient,
    Prescription,
)

_DOSE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mcg|micrograms?|mg|milligrams?|g|grams?)\b", re.IGNORECASE)


def _norm_dose(text: str | None) -> str | None:
    """First dosage in `text`, normalized to e.g. '80mg' / '75mcg'. None if absent."""
    if not text:
        return None
    m = _DOSE_RE.search(text)
    if not m:
        return None
    qty = m.group(1)
    unit = m.group(2).lower()
    if unit.startswith("microgram") or unit == "mcg":
        unit = "mcg"
    elif unit.startswith("milligram") or unit == "mg":
        unit = "mg"
    elif unit.startswith("gram") or unit == "g":
        unit = "g"
    return f"{qty}{unit}"


def match_med(order: str, active: list[Prescription]) -> Prescription | None:
    """Match a requested order string to an active prescription (shared with drafting)."""
    o = order.strip().lower()
    if not o:
        return None
    return next(
        (rx for rx in active if rx.medication_name.lower() in o or o in rx.medication_name.lower()),
        None,
    )


def check_refill(
    *,
    request: ExtractedRequest,
    patient: Patient,
    store,
    policy: ClinicPolicy,
    now: datetime,
) -> EligibilityResult:
    checks: list[EligibilityCheck] = []
    active = store.active_prescriptions_for(patient.id)
    order = (request.orders or [""])[0]

    # 1. Active prescription on file.
    rx = match_med(order, active)
    checks.append(
        EligibilityCheck(
            name="active_prescription",
            passed=rx is not None,
            detail=(f"{rx.medication_name} is active." if rx else f"No active prescription matches '{order or '(none named)'}'."),
        )
    )

    if rx is not None:
        # 2. Dosage approved (script + last-visit notes). Unstated dose -> default.
        approved: set[str] = set()
        if (d := _norm_dose(rx.dosage)):
            approved.add(d)
        last_appt = store.last_completed_appointment(patient.id, now=now)
        if last_appt:
            for am in last_appt.approved_meds:
                if am.medication_name.lower() == rx.medication_name.lower() and (d := _norm_dose(am.dosage)):
                    approved.add(d)
        stated = _norm_dose(request.details)
        dose_ok = stated is None or stated in approved
        checks.append(
            EligibilityCheck(
                name="dosage_approved",
                passed=dose_ok,
                detail=(
                    "No dosage stated; defaulting to the active script."
                    if stated is None
                    else (f"Requested {stated} matches an approved dosage." if dose_ok
                          else f"Requested {stated} is not an approved dosage ({', '.join(sorted(approved)) or 'none on file'}).")
                ),
            )
        )

        # 4. Controlled substance.
        controlled_ok = not (policy.controlled_substance_excluded and rx.controlled)
        checks.append(
            EligibilityCheck(
                name="controlled_substance",
                passed=controlled_ok,
                detail=("Controlled substance — requires provider authorization." if not controlled_ok else "Not a controlled substance."),
            )
        )

        # 6. Drug conflict (established >= threshold is tolerated).
        checks.append(_conflict_check(rx, active, store, policy, now))

        # 7. Refill timing — not requested too early (still has plenty of supply).
        if rx.last_filled is not None:
            days_left = (rx.last_filled + timedelta(days=rx.days_supply) - now.date()).days
            too_soon = days_left > policy.early_refill_buffer_days
            checks.append(EligibilityCheck(
                name="refill_timing",
                passed=not too_soon,
                detail=(f"~{days_left} days of supply remain — refill requested early." if too_soon
                        else "Refill timing is appropriate."),
            ))

        # 8. Prescription not expired (script still valid).
        if rx.valid_until is not None:
            expired = rx.valid_until < now.date()
            checks.append(EligibilityCheck(
                name="prescription_current",
                passed=not expired,
                detail=(f"Prescription expired {rx.valid_until} — needs provider renewal." if expired
                        else "Prescription is current."),
            ))

    # 3. Visit requirement (independent of the specific script).
    checks.append(_visit_check(patient, store, policy, now))

    # 5. Insurance — the patient's on-file plan.
    insured_ok = not policy.accepted_insurance or (patient.insurance_plan in policy.accepted_insurance)
    checks.append(
        EligibilityCheck(
            name="insurance_accepted",
            passed=insured_ok,
            detail=(f"Plan on file ({patient.insurance_plan}) is accepted." if insured_ok
                    else f"Plan on file ({patient.insurance_plan}) is not accepted."),
        )
    )

    eligible = all(c.passed for c in checks)
    flagged = None if eligible else "; ".join(c.detail for c in checks if not c.passed)
    return EligibilityResult(eligible=eligible, checks=checks, flagged_reason=flagged)


def _visit_check(patient: Patient, store, policy: ClinicPolicy, now: datetime) -> EligibilityCheck:
    today = now.date()
    recent = patient.last_visit is not None and (today - patient.last_visit).days <= policy.refill_recent_visit_days
    future = any(
        0 <= (a.start_time.date() - today).days <= policy.refill_future_visit_window_days
        for a in store.future_appointments(patient.id, now=now)
    )
    passed = recent or future
    if recent:
        detail = f"Visited {patient.last_visit} (within {policy.refill_recent_visit_days} days)."
    elif future:
        detail = "A visit is scheduled within the next year."
    else:
        detail = "No recent visit and no upcoming visit on the books."
    return EligibilityCheck(name="visit_requirement", passed=passed, detail=detail)


def _conflict_check(rx: Prescription, active: list[Prescription], store, policy: ClinicPolicy, now: datetime) -> EligibilityCheck:
    conflicting_names = store.conflicts_with(rx.medication_name)
    others = [m for m in active if m.medication_name.lower() in conflicting_names]
    if not others:
        return EligibilityCheck(name="drug_conflict", passed=True, detail="No conflicting active medications.")

    today = now.date()
    unestablished: list[str] = []
    for other in others:
        # Overlap began when the later of the two was prescribed.
        starts = [d for d in (rx.prescribed_date, other.prescribed_date) if d is not None]
        overlap_start = max(starts) if starts else None
        overlap_days = (today - overlap_start).days if overlap_start else 0
        if overlap_days < policy.conflict_established_days:
            unestablished.append(other.medication_name)

    if unestablished:
        return EligibilityCheck(
            name="drug_conflict",
            passed=False,
            detail=f"Potential conflict with {', '.join(unestablished)} (not an established combination) — requires provider review.",
        )
    return EligibilityCheck(
        name="drug_conflict",
        passed=True,
        detail=f"Conflicts with {', '.join(o.medication_name for o in others)} but co-prescribed > {policy.conflict_established_days // 365 or 1}yr — tolerated.",
    )
