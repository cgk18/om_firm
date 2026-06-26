"""Golden (expected) `Intent`s for the seed messages.

These are the correct extractions, hand-written from the transcripts. The eval
harness scores each model's output against them; they double as a canned,
offline extractor so the pipeline can run end-to-end with no API key.

Scored fields are the high-confidence ones (name, DOB, request type, orders,
urgency, request count, and a resolved preferred date where one is expected) —
see app/eval/score.py.
"""

from __future__ import annotations

from datetime import date

from app.contracts import (
    ExtractedRequest,
    Intent,
    PreferredTime,
    RequestType,
    TimeOfDay,
    Urgency,
)


def _one(req: ExtractedRequest, **fields) -> Intent:
    """Single-request intent: request and requests[0] are the same object."""
    return Intent(request=req, requests=[req], **fields)


GOLDEN: dict[str, Intent] = {
    # Clean refill.
    "vm_001": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Lisinopril"], urgency_signal=Urgency.routine),
        first_name="Maria",
        last_name="Garcia",
        date_of_birth=date(1971, 3, 2),
        phone_number="415-555-0142",
    ),
    # Refill, stale visit (eligibility decides that downstream; intake is clean).
    "vm_002": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Metformin"], urgency_signal=Urgency.routine),
        first_name="Robert",
        last_name="Chen",
        date_of_birth=date(1958, 11, 20),
        phone_number="415-555-0188",
    ),
    # Reschedule with a concrete resolved date (July 2 is a Thursday in 2026).
    "vm_003": _one(
        ExtractedRequest(
            type=RequestType.reschedule,
            urgency_signal=Urgency.routine,
            preferred_times=[
                PreferredTime(raw_text="that Thursday, July 2nd, afternoon", date=date(2026, 7, 2), time_of_day=TimeOfDay.afternoon)
            ],
        ),
        first_name="Linda",
        last_name="Nguyen",
        date_of_birth=date(1986, 7, 14),
        phone_number="415-555-0110",
    ),
    # Refill, insurance named (Oscar Health — not accepted, decided downstream).
    "vm_004": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Albuterol"], urgency_signal=Urgency.routine),
        first_name="James",
        last_name="Wilson",
        date_of_birth=date(1990, 2, 9),
        phone_number="415-555-0173",
        insurance_plan="Oscar Health",
    ),
    # Emergency: no refill/reschedule/relay -> unknown type, emergency urgency, no DOB.
    "vm_005": _one(
        ExtractedRequest(type=RequestType.unknown, orders=[], urgency_signal=Urgency.emergency),
        first_name="Patricia",
        last_name="Brown",
        phone_number="415-555-0155",
    ),
    # Refill; caller names a wrong dosage (mismatch decided downstream).
    "vm_006": _one(
        ExtractedRequest(
            type=RequestType.refill,
            details="Refill atorvastatin; caller believes current dose is 80 mg.",
            orders=["Atorvastatin"],
            urgency_signal=Urgency.routine,
        ),
        first_name="David",
        last_name="Kim",
        date_of_birth=date(1979, 12, 5),
        phone_number="415-555-0126",
    ),
    # Unknown patient (not in DB) + drug class only, so orders is empty.
    "vm_007": _one(
        ExtractedRequest(type=RequestType.refill, orders=[], urgency_signal=Urgency.routine),
        first_name="Tom",
        last_name="Bradley",
        date_of_birth=date(1983, 4, 18),
        phone_number="415-555-0199",
    ),
    # Missing fields: first name only, no last name / DOB / callback.
    "vm_008": _one(
        ExtractedRequest(type=RequestType.reschedule, orders=[], urgency_signal=Urgency.routine),
        first_name="Jenny",
    ),
    # Multi-intent: refill (primary) + reschedule. Two requests.
    "vm_009": Intent(
        first_name="Daniel",
        last_name="Foster",
        date_of_birth=date(1974, 8, 9),
        phone_number="415-555-0133",
        request=ExtractedRequest(type=RequestType.refill, orders=["Levothyroxine"], urgency_signal=Urgency.routine),
        requests=[
            ExtractedRequest(type=RequestType.refill, orders=["Levothyroxine"], urgency_signal=Urgency.routine),
            ExtractedRequest(
                type=RequestType.reschedule,
                urgency_signal=Urgency.routine,
                preferred_times=[
                    PreferredTime(raw_text="that Thursday", date=date(2026, 7, 9), time_of_day=TimeOfDay.unknown)
                ],
            ),
        ],
    ),
    # Controlled substance refill (excluded by policy downstream).
    "vm_010": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Alprazolam"], urgency_signal=Urgency.routine),
        first_name="Karen",
        last_name="Diaz",
        date_of_birth=date(1991, 6, 3),
        phone_number="415-555-0147",
    ),
    # Email channel, clean refill.
    "em_001": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Omeprazole"], urgency_signal=Urgency.routine),
        first_name="Angela",
        last_name="Wright",
        date_of_birth=date(1969, 10, 22),
        phone_number="415-555-0161",
    ),
    # Conflict established (tolerated) -> ready.
    "vm_011": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Lisinopril"], urgency_signal=Urgency.routine),
        first_name="Sandra",
        last_name="Lewis",
        date_of_birth=date(1962, 2, 14),
        phone_number="415-555-0150",
    ),
    # Conflict fresh -> needs provider review.
    "vm_012": _one(
        ExtractedRequest(
            type=RequestType.refill,
            details="Refill Sertraline 50 mg.",
            orders=["Sertraline"],
            urgency_signal=Urgency.routine,
        ),
        first_name="Mark",
        last_name="Reyes",
        date_of_birth=date(1980, 3, 22),
        phone_number="415-555-0151",
    ),
    # Future-appointment saves the visit requirement -> ready.
    "vm_013": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Metoprolol"], urgency_signal=Urgency.routine),
        first_name="Olivia",
        last_name="Park",
        date_of_birth=date(1975, 9, 5),
        phone_number="415-555-0152",
    ),
    # Discharged patient -> status gate (no draft).
    "vm_014": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Lisinopril"], urgency_signal=Urgency.routine),
        first_name="Gregory",
        last_name="Hale",
        date_of_birth=date(1968, 4, 25),
        phone_number="415-555-0153",
    ),
    # Refill too soon (plenty of supply left).
    "vm_015": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Lisinopril"], urgency_signal=Urgency.routine),
        first_name="Brian",
        last_name="Lee",
        date_of_birth=date(1983, 7, 19),
        phone_number="415-555-0154",
    ),
    # Prescription expired.
    "vm_016": _one(
        ExtractedRequest(type=RequestType.refill, orders=["Atorvastatin"], urgency_signal=Urgency.routine),
        first_name="Carol",
        last_name="White",
        date_of_birth=date(1959, 12, 1),
        phone_number="415-555-0156",
    ),
    # Routine message relay -> ready.
    "vm_017": _one(
        ExtractedRequest(
            type=RequestType.message_relay,
            details="Let Dr. Patel know the patient will be traveling next month and may miss the usual check-in.",
            urgency_signal=Urgency.routine,
        ),
        first_name="Henry",
        last_name="Adams",
        date_of_birth=date(1972, 3, 8),
        phone_number="415-555-0157",
    ),
    # Clinical message relay (medication reaction) -> needs_action.
    "vm_018": _one(
        ExtractedRequest(
            type=RequestType.message_relay,
            details="Patient reports a reaction to the new blood pressure medication — nausea and a rash.",
            urgency_signal=Urgency.routine,
        ),
        first_name="Diane",
        last_name="Cooper",
        date_of_birth=date(1980, 10, 14),
        phone_number="415-555-0158",
    ),
}


def canned_extract(message) -> Intent:
    """Offline stand-in extractor: returns the golden Intent for a seed message.
    Lets the pipeline run end-to-end with no API key."""
    intent = GOLDEN[message.id].model_copy(deep=True)
    intent.transcript = message.transcript or message.raw_body or ""
    return intent
