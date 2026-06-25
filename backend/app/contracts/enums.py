from __future__ import annotations

from enum import Enum


class Channel(str, Enum):
    """Where an inbound message came from. Voicemail is the hero; email runs the
    same pipeline. Channel-agnostic intake by design."""

    voicemail = "voicemail"
    email = "email"


class RequestType(str, Enum):
    """What intake *extracts* from a message (request granularity).

    message_relay is detected but PARKED in v1 — the orchestrator escalates it
    rather than drafting. Kept in the vocabulary so a relay is never mis-routed
    as a refill/reschedule.
    """

    refill = "refill"
    reschedule = "reschedule"
    message_relay = "message_relay"
    unknown = "unknown"


class TaskType(str, Enum):
    """What the orchestrator *routes* a task to (workflow granularity)."""

    refill = "refill"
    reschedule = "reschedule"
    escalate = "escalate"


class TaskStatus(str, Enum):
    """Lifecycle of a reviewable task. Nothing auto-executes — `done` means a
    human approved the draft and will act on it in their own system."""

    needs_review = "needs_review"
    done = "done"
    rejected = "rejected"
    escalated = "escalated"


class Urgency(str, Enum):
    """Clinical urgency of a request — distinct from request *type*. `emergency`
    bypasses automation and escalates immediately."""

    routine = "routine"
    urgent = "urgent"
    emergency = "emergency"
    unknown = "unknown"


class TimeOfDay(str, Enum):
    morning = "morning"
    afternoon = "afternoon"
    evening = "evening"
    anytime = "anytime"
    unknown = "unknown"
