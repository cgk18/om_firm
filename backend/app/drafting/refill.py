"""Refill drafting — turns a matched prescription + eligibility result into a
`Draft` (the proposed action) plus `Blocker`s (the ACTION NEEDED items).

Templated for v1 (no LLM): the data is already structured, so the rendered text
is deterministic and demo-safe. The structured action always proposes the
provider-approved script — so even a blocked dosage-mismatch proposes the
*correct* refill, with a blocker flagging the discrepancy.
"""

from __future__ import annotations

from app.contracts import (
    Blocker,
    Draft,
    EligibilityResult,
    ExtractedRequest,
    Patient,
    Prescription,
    RefillAction,
)

# Failed eligibility check -> (blocker code, staff-facing imperative).
_CHECK_TO_BLOCKER: dict[str, tuple[str, str]] = {
    "active_prescription": ("medication_not_on_file", "Verify the requested medication"),
    "dosage_approved": ("dosage_mismatch", "Confirm dosage with provider"),
    "visit_requirement": ("schedule_visit", "Schedule an appointment"),
    "controlled_substance": ("controlled_substance", "Provider authorization required"),
    "insurance_accepted": ("insurance_not_accepted", "Verify insurance"),
    "drug_conflict": ("drug_conflict", "Provider review — drug interaction"),
    "refill_timing": ("refill_too_soon", "Refill requested early — confirm timing"),
    "prescription_current": ("prescription_expired", "Prescription expired — needs provider renewal"),
}


def refill_blockers(eligibility: EligibilityResult) -> list[Blocker]:
    """One Blocker per failed check, in check order."""
    out: list[Blocker] = []
    for c in eligibility.checks:
        if not c.passed:
            code, label = _CHECK_TO_BLOCKER.get(c.name, (c.name, "Review required"))
            out.append(Blocker(code=code, label=label, detail=c.detail))
    return out


def draft_refill(
    *,
    request: ExtractedRequest,
    patient: Patient,
    rx: Prescription | None,
    provider_name: str | None,
    blockers: list[Blocker],
) -> Draft:
    """Build the refill Draft. `rx` is the matched active prescription (None only
    if the med isn't on file — then we draft against the requested name)."""
    med = rx.medication_name if rx else (request.orders or ["the requested medication"])[0]
    dosage = rx.dosage if rx else ""
    instructions = rx.instructions if rx else ""
    provider_id = rx.provider_id if rx else None

    structured = RefillAction(
        patient_id=patient.id,
        medication=med,
        dosage=dosage,
        instructions=instructions,
        provider_id=provider_id,
    )

    headline = f"Refill {med}{f' {dosage}' if dosage else ''} for {patient.full_name}"
    to_provider = f" → send to {provider_name} for signature" if provider_name else ""
    lines = [f"{headline}{to_provider}."]
    if blockers:
        lines.append("")
        lines.append("ACTION NEEDED before approval:")
        lines.extend(f"  • {b.label} — {b.detail}" for b in blockers)
    else:
        lines.append("Ready to approve.")

    return Draft(structured=structured, rendered="\n".join(lines))
