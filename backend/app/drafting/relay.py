"""Message-relay drafting + triage.

A relay drafts a note to forward to the patient's provider. Most relays are
routine -> `ready` (one-click send). The agent's real job is to catch the middle
tier — clinically significant content (symptoms / side effects / a medication
reaction) that the upstream emergency hard-stop does NOT catch — and flag it so
staff escalate it to the provider promptly.
"""

from __future__ import annotations

import re

from app.contracts import Blocker, Draft, MessageRelayAction

# Sub-emergency clinical signals. (True 911-level emergencies are pulled out
# upstream by the orchestrator's emergency hard-stop.)
_CLINICAL_KEYWORDS = [
    "reaction", "side effect", "side effects", "dizzy", "dizziness", "nausea",
    "nauseous", "vomiting", "rash", "swelling", "worse", "worsening", "fever",
    "bleeding", "symptom", "symptoms", "allergic",
]
_CLINICAL_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in _CLINICAL_KEYWORDS) + r")\b")


def is_clinical(request, transcript: str) -> bool:
    """True if the relay carries clinical content the provider should review."""
    if request.urgency_signal.value == "urgent":
        return True
    text = f"{transcript or ''} {request.details or ''}".lower()
    return bool(_CLINICAL_RE.search(text))


def relay_blockers(*, request, transcript: str, used_fallback: bool) -> list[Blocker]:
    blockers: list[Blocker] = []
    if is_clinical(request, transcript):
        blockers.append(Blocker(
            code="clinical_review",
            label="Clinical content — escalate to the provider",
            detail="The message describes symptoms or a medication reaction; the provider should review it promptly.",
        ))
    if used_fallback:
        blockers.append(Blocker(
            code="provider_fallback",
            label="Confirm the recipient",
            detail="No usual provider on file — routed to the on-duty provider; confirm who should receive this.",
        ))
    return blockers


def draft_relay(*, request, patient, provider_id: str | None, transcript: str, store, used_fallback: bool) -> Draft:
    body = (request.details or transcript or "").strip()
    structured = MessageRelayAction(patient_id=patient.id, provider_id=provider_id, message=body)

    provider_name = store.provider(provider_id).name if (provider_id and store.provider(provider_id)) else "the provider"
    lines = [f"Relay to {provider_name}:", f"  {patient.full_name} reports: {body}"]

    blockers = relay_blockers(request=request, transcript=transcript, used_fallback=used_fallback)
    if blockers:
        lines.append("")
        lines.append("ACTION NEEDED before sending:")
        lines.extend(f"  • {b.label} — {b.detail}" for b in blockers)
    else:
        lines.append("Ready to send.")

    return Draft(structured=structured, rendered="\n".join(lines))
