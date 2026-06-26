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
from app.drafting.relay import draft_relay, relay_blockers
from app.drafting.reschedule import draft_reschedule, reschedule_blockers
from app.eligibility import check_refill
from app.eligibility.refill import match_med
from app.eligibility.reschedule import assess_reschedule


class _NullHolds:
    """No-op holds used until a real HoldStore is passed in: never conflicts,
    never reserves. Lets reschedule run end-to-end before holds.py is finished."""

    def conflicts(self, *a, **k) -> bool:
        return False

    def reserve(self, *a, **k) -> None:
        return None

# Keyword backstop under the LLM urgency signal — high recall on purpose: an
# over-escalation is acceptable, a missed emergency is not. Tunable.
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "cannot breathe", "trouble breathing",
    "stroke", "unconscious", "passed out", "numb", "numbness",
    "suicidal", "kill myself", "overdose", "seizure", "heavy bleeding",
]
# Word-boundary match so "numb" doesn't fire on "number", etc.
_EMERGENCY_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in EMERGENCY_KEYWORDS) + r")\b")


def orchestrate(intent: Intent, message: Message, *, store, policy, now: datetime, holds=None) -> list[Task]:
    holds = holds or _NullHolds()
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

    # 3. Patient-status gate — only draft actions for ACTIVE patients. A discharged /
    #    inactive / deceased record must never produce a ready-to-approve action.
    if patient.status != "active":
        blocker = Blocker(
            code="patient_inactive",
            label=f"Patient record is '{patient.status}' — verify before acting",
            detail=f"This patient is marked '{patient.status}' in the system. Do not process without confirming their status.",
        )
        return [
            _task(
                message_id=message.id, patient_id=patient.id, patient_name=patient.full_name,
                type=_task_type(req), status=TaskStatus.needs_action, request=req,
                blockers=[blocker], flagged_reason=blocker.detail,
                agent_summary=f"{patient.full_name} — record is {patient.status}, verify before acting.",
            )
            for req in requests
        ]

    # 4. Active & matched — dispatch each request by type.
    return [_dispatch(req, intent, message, patient, basis, store=store, policy=policy, now=now, holds=holds) for req in requests]


def _dispatch(req, intent, message, patient, basis, *, store, policy, now, holds) -> Task:
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

    if req.type.value == "reschedule":
        assessment = assess_reschedule(request=req, patient=patient, store=store, holds=holds, policy=policy, now=now)
        blockers = reschedule_blockers(assessment)
        draft = draft_reschedule(request=req, patient=patient, assessment=assessment, store=store)
        if assessment.eligibility.eligible and not blockers:
            status, summary = TaskStatus.ready, f"{name} — reschedule, ready to approve."
        else:
            label = blockers[0].label if blockers else "review"
            status, summary = TaskStatus.needs_action, f"{name} — reschedule, needs action: {label}."
        task = _task(
            message_id=message.id, patient_id=patient.id, patient_name=name,
            type=TaskType.reschedule, status=status, request=req,
            eligibility=assessment.eligibility, draft=draft, blockers=blockers, agent_summary=summary,
        )
        # Reserve the proposed slot against this task so no one else takes it.
        if assessment.proposed_start and assessment.provider_id:
            holds.reserve(assessment.provider_id, assessment.proposed_start, assessment.proposed_end, task.id)
        return task

    if req.type.value == "message_relay":
        transcript = message.transcript or message.raw_body or ""
        provider_id = patient.primary_provider_id
        used_fallback = provider_id is None
        if used_fallback:
            od = store.on_duty_provider()
            provider_id = od.id if od else None
        draft = draft_relay(request=req, patient=patient, provider_id=provider_id,
                            transcript=transcript, store=store, used_fallback=used_fallback)
        blockers = relay_blockers(request=req, transcript=transcript, used_fallback=used_fallback)
        if blockers:
            status, summary = TaskStatus.needs_action, f"{name} — relay to provider, needs review: {blockers[0].label}."
        else:
            status, summary = TaskStatus.ready, f"{name} — relay to provider, ready to send."
        return _task(
            message_id=message.id, patient_id=patient.id, patient_name=name,
            type=TaskType.message_relay, status=status, request=req,
            draft=draft, blockers=blockers, agent_summary=summary,
        )

    # unknown — needs a human.
    blocker = Blocker(code="manual_review", label="Manual review",
                      detail="Request type could not be determined.")
    return _task(
        message_id=message.id, patient_id=patient.id, patient_name=name,
        type=TaskType.escalate, status=TaskStatus.needs_action, request=req,
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
    return {
        "refill": TaskType.refill,
        "reschedule": TaskType.reschedule,
        "message_relay": TaskType.message_relay,
    }.get(req.type.value, TaskType.escalate)


def _task(**kwargs) -> Task:
    return Task(**kwargs)
