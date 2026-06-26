"""Reschedule drafting — RescheduleAssessment -> Draft + Blockers.

Same pattern as drafting/refill.py. A clean reschedule (requested slot free, same
provider, not far out) has no blockers -> the Task is `ready`.
"""

from __future__ import annotations

from app.contracts import Blocker, Draft, RescheduleAction


def draft_reschedule(*, request, patient, assessment, store) -> Draft:
    provider_name = None
    if assessment.provider_id and store.provider(assessment.provider_id):
        provider_name = store.provider(assessment.provider_id).name

    structured = RescheduleAction(
        patient_id=patient.id,
        provider_id=assessment.provider_id,
        new_start=assessment.proposed_start,
        new_end=assessment.proposed_end,
        cancel_appointment_id=assessment.cancel_appointment_id,
    )

    when = f"{assessment.proposed_start:%a %b %d, %I:%M %p}" if assessment.proposed_start else "(no slot found)"
    if assessment.cancel_appointment_id is None:
        head = f"Book a new appointment for {patient.full_name} on {when}"
    else:
        head = f"Move {patient.full_name}'s appointment to {when}"
    head += f" with {provider_name}." if provider_name else "."
    lines = [head]
    if not assessment.requested_was_available and assessment.proposed_start:
        lines.append("Requested time wasn't open — proposed the nearest slot.")
    if assessment.switched_provider:
        lines.append(f"Original provider was full — proposed covering provider {provider_name}.")

    blockers = reschedule_blockers(assessment)
    if blockers:
        lines.append("")
        lines.append("ACTION NEEDED before approval:")
        lines.extend(f"  • {b.label} — {b.detail}" for b in blockers)
    else:
        lines.append("Ready to approve.")

    return Draft(structured=structured, rendered="\n".join(lines))


def reschedule_blockers(assessment) -> list[Blocker]:
    blockers: list[Blocker] = []
    if not assessment.eligibility.eligible:
        blockers.append(Blocker(code="no_slot_available", label="Find a slot manually / call the patient",
                                detail=assessment.eligibility.flagged_reason or "No slot available."))
        return blockers
    if not assessment.requested_was_available:
        blockers.append(Blocker(code="confirm_proposed_time", label="Confirm the proposed time with the patient",
                                detail="Their requested time was taken; a nearby slot is proposed."))
    if assessment.switched_provider:
        blockers.append(Blocker(code="provider_changed", label="Confirm the covering provider",
                                detail="The original provider was full; a covering provider is proposed."))
    if assessment.far_out:
        blockers.append(Blocker(code="appointment_far_out", label="Confirm — appointment is over a month out",
                                detail="The soonest slot is more than a month away; the patient may prefer another option."))
    if assessment.repeated_reschedule:
        blockers.append(Blocker(code="repeated_reschedule", label="Review — appointment rescheduled repeatedly",
                                detail="This appointment has been moved several times; confirm the patient isn't deferring a needed visit."))
    return blockers
