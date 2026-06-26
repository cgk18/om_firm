"""Intake stage — a pure transform: Message -> Intent.

Reads `message.transcript` (filled by transcription for voicemail, or copied
from the email body) and returns a validated `Intent`. No routing, no
persistence, no HTTP — those belong to the orchestrator and the tasks repo.

Implementation note: we ask the model for JSON and validate it into `Intent`,
rather than using structured outputs (`messages.parse`). Constrained decoding
hangs on our nested `Intent` schema (deep nesting + optional date fields), so
prompt-and-parse is the reliable path — with one repair retry on a bad parse.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from pydantic import ValidationError

from app.contracts import Intent, Message

# Starting model per the cost/performance discussion: extraction is short and
# mechanical, which is Haiku's wheelhouse. The eval harness (app/eval) confirms
# this empirically against the seed set; bump to claude-sonnet-4-6 only on
# measured failures. One-line swap.
INTAKE_MODEL = "claude-haiku-4-5"
MAX_TOKENS = 1024

SYSTEM_PROMPT = """
You are the Intake Agent for a clinic's patient-message triage system. You read a
single inbound message (a voicemail transcript or an email) and extract only the
facts explicitly stated. Never infer identity, insurance, dates, phone numbers, or
request details that are not actually present. If a field is not stated, use null
for scalars and [] for arrays.

Identity and contact:
- first_name, last_name: as stated.
- date_of_birth: YYYY-MM-DD only if enough information is given; otherwise null.
- phone_number: the stated callback number, as digits or a readable phone string.
- insurance_plan: only if the caller names their plan.

Requests:
- `request` is the primary (first) request. `requests` contains every distinct
  request in the message, in the order stated. If there is exactly one request,
  `requests` holds one object identical to `request`.
- For multiple asks (for example a refill plus a reschedule), create one request
  object per workflow item.
- request.type is one of: refill, reschedule, message_relay, unknown. This is the
  workflow category, NOT medical urgency — never put emergency here.
    - refill: the caller asks to refill or renew a medication.
    - reschedule: the caller asks to move, change, or cancel an appointment.
    - message_relay: the caller asks the clinic to notify, tell, or relay
      something to a provider (including side effects or symptoms to pass along).
    - unknown: acute symptoms or safety concerns with no refill, reschedule, or
      relay request.
- request.details: a concise factual summary of what the caller asked for.
- request.orders: only medications or items the caller explicitly asks the clinic
  to refill, order, or act on, for example ["Lisinopril"]. Use [] when none are
  named. Do NOT include medications mentioned only as history, context, current
  medications, side effects, or symptoms. Do NOT include dosages. If the caller
  names only a drug class ("my blood pressure medication") with no specific drug,
  use [].
- request.urgency_signal is one of: routine, urgent, emergency, unknown — the
  clinical urgency, kept separate from request.type.

Preferred times (for reschedules):
- preferred_times is an array of objects, each with raw_text, date, start_time,
  time_of_day. Never plain strings.
- raw_text: the caller's original phrase, for example "July 2nd in the afternoon".
- The user message includes reference_date (the date the message was received,
  YYYY-MM-DD) and reference_weekday. Treat reference_date as "today" and resolve
  every relative or partial date phrase against it.
- date: a concrete YYYY-MM-DD whenever the caller names a specific day, even
  relatively; null only when no day is given ("sometime next week", "in the
  morning").
    - "today" is reference_date; "tomorrow" is reference_date plus one day; a
      weekday name ("Tuesday", "this Tuesday", "next Tuesday") is the soonest date
      strictly after reference_date on that weekday, and the resolved weekday must
      match the named one.
    - A month and day with no year ("July 2nd") uses the year that makes the date
      fall on or after reference_date.
- start_time: 24-hour HH:MM when a specific time is stated; otherwise null.
- time_of_day is one of: morning, afternoon, evening, anytime, unknown.
- Example (reference_date 2026-06-25): "July 2nd at 3 PM" becomes
  {"raw_text": "July 2nd at 3 PM", "date": "2026-07-02", "start_time": "15:00",
   "time_of_day": "afternoon"}.

missing_fields: list any required intake fields that are absent, drawn from:
first_name, last_name, date_of_birth, phone_number, insurance_plan,
request.details.

OUTPUT: return ONLY a single JSON object — no markdown, no code fences, no
commentary — with exactly these top-level keys: first_name, last_name,
date_of_birth, phone_number, insurance_plan, request, requests, missing_fields.
`request` and every item of `requests` is an object with keys: type, details,
orders, preferred_times, urgency_signal. Each preferred_times item has keys:
raw_text, date, start_time, time_of_day. Use null for unknown scalars and [] for
empty arrays. Do not include a transcript field.
""".strip()


def _default_client() -> Any:
    import anthropic

    return anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def extract_intent(
    message: Message,
    *,
    client: Any | None = None,
    model: str = INTAKE_MODEL,
    reference_date: date | None = None,
) -> Intent:
    """Extract a structured `Intent` from one message.

    `client` is injectable for tests/offline runs. `reference_date` defaults to
    the message's received date — the anchor for resolving relative date phrases.
    """
    transcript = message.transcript or message.raw_body or ""
    ref = reference_date or message.received_at.date()

    if client is None:
        client = _default_client()

    raw = _call_model(client, model, transcript, ref)
    try:
        intent = Intent(**_parse_json(raw))
    except (ValidationError, ValueError):
        # One repair retry: the model occasionally emits malformed JSON or a
        # field that won't validate. Re-ask once with the prior output to fix.
        raw = _call_model(client, model, transcript, ref, prior=raw)
        intent = Intent(**_parse_json(raw))

    intent.transcript = transcript  # carry the source text; we don't ask the model for it
    return intent


def _call_model(client: Any, model: str, transcript: str, ref: date, *, prior: str | None = None) -> str:
    content: dict[str, Any] = {
        "transcript": transcript,
        "reference_date": ref.isoformat(),
        "reference_weekday": ref.strftime("%A"),
    }
    if prior is not None:
        content["note"] = "Your previous reply was not valid JSON in the required shape. Return ONLY the corrected JSON object."
        content["previous_reply"] = prior

    message = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        temperature=0,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # stable prefix — cache it
            }
        ],
        messages=[{"role": "user", "content": json.dumps(content)}],
    )
    return "".join(b.text for b in message.content if getattr(b, "type", None) == "text").strip()


def _parse_json(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data
