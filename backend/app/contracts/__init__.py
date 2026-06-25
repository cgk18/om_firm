"""Shared schema backbone for the draft-and-route pipeline.

Import everything from here: `from app.contracts import Task, Draft, ...`.
Layered as: message → (intake) intent → task → draft, with patient + clinic
policy as read-only/config inputs.
"""

from __future__ import annotations

from .clinic_policy import ClinicPolicy, default_policy
from .draft import Blocker, Draft, DraftAction, RefillAction, RescheduleAction
from .enums import (
    Channel,
    RequestType,
    TaskStatus,
    TaskType,
    TimeOfDay,
    Urgency,
)
from .intent import ExtractedRequest, Intent, PreferredTime
from .message import Message
from .patient import Appointment, Patient, Prescription, Provider
from .task import EligibilityCheck, EligibilityResult, Task

__all__ = [
    # enums
    "Channel",
    "RequestType",
    "TaskType",
    "TaskStatus",
    "Urgency",
    "TimeOfDay",
    # message
    "Message",
    # intent
    "Intent",
    "ExtractedRequest",
    "PreferredTime",
    # patient / seeded EHR
    "Patient",
    "Prescription",
    "Appointment",
    "Provider",
    # draft
    "Draft",
    "Blocker",
    "DraftAction",
    "RefillAction",
    "RescheduleAction",
    # task
    "Task",
    "EligibilityResult",
    "EligibilityCheck",
    # policy
    "ClinicPolicy",
    "default_policy",
]
