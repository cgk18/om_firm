"""Reschedule drafting — RescheduleAssessment -> Draft + Blockers.   ★ HOMEWORK ★

Same pattern as drafting/refill.py. A clean reschedule (requested slot was free,
same provider, not far out) has NO blockers -> the Task is `ready`.
"""

from __future__ import annotations

from app.contracts import Blocker, Draft, RescheduleAction


def draft_reschedule(*, request, patient, assessment, store) -> Draft:
    # TODO: structured = RescheduleAction(
    #           patient_id=patient.id, provider_id=assessment.provider_id,
    #           new_start=assessment.proposed_start, new_end=assessment.proposed_end,
    #           cancel_appointment_id=assessment.cancel_appointment_id)   # None = new booking
    # TODO: provider_name = store.provider(assessment.provider_id).name
    # TODO: build `lines` (the rendered text):
    #         - "Move {patient.full_name}'s appointment to {start:%a %b %d, %I:%M %p} with {provider_name}."
    #           (or "Book a new appointment for {patient.full_name} ..." when cancel id is None)
    #         - if not assessment.requested_was_available: "Requested time wasn't open — proposed the nearest slot."
    #         - if assessment.switched_provider: "Dr. <primary> is full; proposed covering provider {provider_name}."
    #         - then an ACTION NEEDED list if there are blockers, else "Ready to approve."
    # TODO: return Draft(structured=structured, rendered="\n".join(lines))
    raise NotImplementedError


def reschedule_blockers(assessment) -> list[Blocker]:
    blockers: list[Blocker] = []
    # TODO: if not assessment.requested_was_available:
    #           blockers.append(Blocker("confirm_proposed_time", "Confirm the proposed time with the patient", "<why>"))
    # TODO: if assessment.switched_provider:
    #           blockers.append(Blocker("provider_changed", "Confirm the covering provider", "<why>"))
    # TODO: if assessment.far_out:
    #           blockers.append(Blocker("appointment_far_out", "Confirm — appointment is over a month out", "<why>"))
    # TODO (optional): if not assessment.eligibility.eligible:
    #           blockers.append(Blocker("no_slot_available", "Find a slot manually / call the patient", "<why>"))
    # TODO: return blockers
    raise NotImplementedError
