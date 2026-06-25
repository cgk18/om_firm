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
    """Attention level of a task. Because every task carries a draft, status
    conveys *how much human attention is needed*, not whether a draft exists.
    The *why* lives in `flagged_reason` + draft blockers; status carries only the
    lane. Nothing auto-executes — `approved` means a human approved the draft and
    will act on it in their own system.

    Active lanes: ready / needs_action / urgent.  Terminal: approved / dismissed.
    """

    ready = "ready"  # drafted, all checks pass — one-click approve
    needs_action = "needs_action"  # drafted, but blockers must clear first (incl. ambiguous / no patient match)
    urgent = "urgent"  # emergency / safety — jump the queue
    approved = "approved"  # human approved; they execute in their own system
    dismissed = "dismissed"  # rejected / no action needed


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
