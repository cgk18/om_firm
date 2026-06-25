from __future__ import annotations

import datetime

from pydantic import BaseModel, Field

from .enums import RequestType, TimeOfDay, Urgency


class PreferredTime(BaseModel):
    """A time the caller asked for, with relative phrases already resolved by
    intake against the message's reference date."""

    raw_text: str
    # `datetime.date` (not a bare `date`) — the field name `date` would otherwise
    # shadow the type and break annotation resolution under `from __future__`.
    date: datetime.date | None = None
    start_time: str | None = None  # "HH:MM" 24-hour, when a specific time is stated
    time_of_day: TimeOfDay = TimeOfDay.unknown


class ExtractedRequest(BaseModel):
    """One distinct request inside a message (a voicemail may contain several)."""

    type: RequestType = RequestType.unknown
    details: str = ""
    orders: list[str] = Field(default_factory=list)  # meds/items the caller asks us to act on
    preferred_times: list[PreferredTime] = Field(default_factory=list)
    urgency_signal: Urgency = Urgency.unknown


class Intent(BaseModel):
    """Structured output of the intake LLM extraction over one message.

    `request` is the primary/first request; `requests` holds every distinct
    request. Multi-intent messages are handled by the orchestrator looping over
    `requests` (one task per request) — no agentic routing needed.
    """

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    phone_number: str | None = None
    insurance_plan: str | None = None
    request: ExtractedRequest = Field(default_factory=ExtractedRequest)
    requests: list[ExtractedRequest] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    transcript: str = ""
