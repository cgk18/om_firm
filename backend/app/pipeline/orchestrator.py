"""Orchestrator — the linear, deterministic spine.

Intent + Message -> one or more Tasks. In order: emergency hard-stop, two-factor
patient match, then loop over the extracted requests dispatching each by type.
Multi-intent calls become multiple independent tasks that share `message_id`.

v1 scope: refill is wired end-to-end; reschedule / message_relay / unknown are
needs_action placeholders until those drafters exist.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.contracts import (
    Blocker,
    ExtractedRequest,
    Intent,
    Message,
    Task,
    TaskStatus,
    TaskType,
    Urgency,
)
from app.drafting import draft_refill, refill_blockers
from app.eligibility import check_refill
from app.eligibility.refill import match_med

# Keyword backstop under the LLM urgency signal — high recall on purpose: an
# over-escalation is acceptable, a missed emergency is not. Tunable.
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "trouble breathing",
    "stroke", "unconscious", "passed out", "numb", "numbness",
    "suicidal", "kill myself", "overdose", "seizure", "heavy bleeding",
]
# Word-boundary match so "numb" doesn't fire on "number", etc.
_EMERGENCY_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in EMERGENCY_KEYWORDS) + r")\b")


def orchestrate(intent: Intent, message: Message, *, store, policy, now: datetime) -> list[Task]:
    transcript = message.transcript or message.raw_body or ""
    requests = intent.requests or [intent.request]
    stated_name = " ".join(x for x in [intent.first_name, intent.last_name] if x) or "Unknown caller"

    # 1. Emergency hard-stop — trumps everything, one urgent task.
    if _is_emergency(intent, transcript):
        return [
            _task(
                message_id=message.id,
                patient_id=None,
                patient_name=stated_name,
                type=TaskType.escalate,
                status=TaskStatus.urgent,
                request=intent.request,
                flagged_reason="Emergency symptoms mentioned — call the patient immediately.",
                agent_summary=f"{stated_name} — possible emergency, call immediately.",
            )
        ]

    # 2. Two-factor patient match.
    patient, status, basis = store.resolve_patient(
        intent.first_name, intent.last_name, intent.date_of_birth, intent.phone_number
    )
    if patient is None:
        blocker = _identity_blocker(status)
        return [
            _task(
                message_id=message.id,
                patient_id=None,
                patient_name=stated_name,
                type=_task_type(req),
                status=TaskStatus.needs_action,
                request=req,
                blockers=[blocker],
                flagged_reason=blocker.detail,
                agent_summary=f"{stated_name} — {blocker.label.lower()}.",
            )
            for req in requests
        ]

    # 3. Matched — dispatch each request by type.
    return [_dispatch(req, intent, message, patient, basis, store=store, policy=policy, now=now) for req in requests]


def _dispatch(req, intent, message, patient, basis, *, store, policy, now) -> Task:
    name = patient.full_name
    if req.type.value == "refill":
        active = store.active_prescriptions_for(patient.id)
        order = (req.orders or [""])[0]
        rx = match_med(order, active)
        eligibility = check_refill(request=req, patient=patient, store=store, policy=policy, now=now)
        blockers = refill_blockers(eligibility)
        provider_name = store.provider(rx.provider_id).name if rx and store.provider(rx.provider_id) else None
        draft = draft_refill(request=req, patient=patient, rx=rx, provider_name=provider_name, blockers=blockers)
        med = rx.medication_name if rx else (order or "medication")
        if eligibility.eligible:
            summary = f"{name} — refill {med}, ready to approve."
            status = TaskStatus.ready
        else:
            summary = f"{name} — refill {med}, needs action: {blockers[0].label}."
            status = TaskStatus.needs_action
        return _task(
            message_id=message.id, patient_id=patient.id, patient_name=name,
            type=TaskType.refill, status=status, request=req,
            eligibility=eligibility, draft=draft, blockers=blockers, agent_summary=summary,
        )

    # Reschedule / relay / unknown — placeholders until their drafters exist.
    if req.type.value == "reschedule":
        blocker = Blocker(code="manual_reschedule", label="Handle reschedule manually",
                          detail="Reschedule drafting is not yet automated.")
        ttype = TaskType.reschedule
    elif req.type.value == "message_relay":
        blocker = Blocker(code="manual_relay", label="Relay to provider manually",
                          detail="Message relay is out of v1 scope.")
        ttype = TaskType.escalate
    else:
        blocker = Blocker(code="manual_review", label="Manual review",
                          detail="Request type could not be determined.")
        ttype = TaskType.escalate

    return _task(
        message_id=message.id, patient_id=patient.id, patient_name=name,
        type=ttype, status=TaskStatus.needs_action, request=req,
        blockers=[blocker], agent_summary=f"{name} — {blocker.label.lower()}.",
    )


def _is_emergency(intent: Intent, transcript: str) -> bool:
    by_llm = any(r.urgency_signal == Urgency.emergency for r in (intent.requests or [intent.request]))
    by_keyword = bool(_EMERGENCY_RE.search(transcript.lower()))
    return by_llm or by_keyword


def _identity_blocker(status: str) -> Blocker:
    if status == "insufficient_info":
        return Blocker(
            code="verify_identity",
            label="Verify the patient's identity",
            detail="Not enough identifying details — need at least two of name, date of birth, or callback number.",
        )
    return Blocker(
        code="no_patient_match",
        label="Find the patient / verify identity",
        detail="Could not match the caller to a patient in the system.",
    )


def _task_type(req: ExtractedRequest) -> TaskType:
    return {"refill": TaskType.refill, "reschedule": TaskType.reschedule}.get(req.type.value, TaskType.escalate)


def _task(**kwargs) -> Task:
    return Task(**kwargs)
