"""Loads the seeded demo "EHR" + inbound voicemails into validated contract
models. This is the read-only stand-in for a clinic's chart — nothing is ever
written back to it.

`REFERENCE_NOW` is the demo's "today": every relative date phrase in the seeded
transcripts ("next Thursday", "the 30th") resolves against it, so the demo is
reproducible regardless of the wall clock.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.contracts import (
    Appointment,
    Channel,
    Message,
    Patient,
    Prescription,
    Provider,
)

SEED_DIR = Path(__file__).resolve().parent

# Demo "today". Keep in sync with the dates baked into the seeded transcripts.
REFERENCE_NOW = datetime(2026, 6, 25, 9, 0, tzinfo=timezone.utc)


def _load(name: str) -> list[dict]:
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def _norm_phone(phone: str | None) -> str | None:
    """Last 10 digits, so '(415) 555-0142' and '415-555-0142' compare equal."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return digits[-10:] if len(digits) >= 10 else None


class SeedStore:
    """In-memory, read-only view of the seeded EHR with simple lookups."""

    def __init__(self) -> None:
        self.providers: list[Provider] = [Provider(**p) for p in _load("providers.json")]
        self.patients: list[Patient] = [Patient(**p) for p in _load("patients.json")]
        self.prescriptions: list[Prescription] = [
            Prescription(**p) for p in _load("prescriptions.json")
        ]
        self.appointments: list[Appointment] = [
            Appointment(**a) for a in _load("appointments.json")
        ]
        # Curated demo conflict pairs, normalized to lowercase frozensets.
        raw = json.loads((SEED_DIR / "drug_conflicts.json").read_text(encoding="utf-8"))
        self.conflict_pairs: list[frozenset[str]] = [
            frozenset(m.lower() for m in pair) for pair in raw["conflicts"]
        ]

    def patient(self, patient_id: str) -> Patient | None:
        return next((p for p in self.patients if p.id == patient_id), None)

    def provider(self, provider_id: str) -> Provider | None:
        return next((p for p in self.providers if p.id == provider_id), None)

    def prescriptions_for(self, patient_id: str) -> list[Prescription]:
        return [rx for rx in self.prescriptions if rx.patient_id == patient_id]

    def active_prescriptions_for(self, patient_id: str) -> list[Prescription]:
        return [rx for rx in self.prescriptions_for(patient_id) if rx.active]

    def appointments_for(self, patient_id: str) -> list[Appointment]:
        return [a for a in self.appointments if a.patient_id == patient_id]

    def scheduled_for_provider(self, provider_id: str) -> list[Appointment]:
        return [
            a
            for a in self.appointments
            if a.provider_id == provider_id and a.status == "scheduled"
        ]

    def last_completed_appointment(self, patient_id: str, *, now: datetime = REFERENCE_NOW) -> Appointment | None:
        """Most recent completed visit at or before `now` — the source of
        provider-approved dosages ("doctor notes from the last appointment")."""
        past = [
            a
            for a in self.appointments_for(patient_id)
            if a.status == "completed" and a.start_time <= now
        ]
        return max(past, default=None, key=lambda a: a.start_time)

    def future_appointments(self, patient_id: str, *, now: datetime = REFERENCE_NOW) -> list[Appointment]:
        """Upcoming scheduled appointments after `now`."""
        return [
            a
            for a in self.appointments_for(patient_id)
            if a.status == "scheduled" and a.start_time > now
        ]

    def conflicts_with(self, medication_name: str) -> set[str]:
        """Lowercased set of medications that conflict with the given med."""
        med = medication_name.strip().lower()
        result: set[str] = set()
        for pair in self.conflict_pairs:
            if med in pair:
                result |= pair - {med}
        return result

    def resolve_patient(self, first_name, last_name, date_of_birth, phone) -> tuple[Patient | None, str, str | None]:
        """Two-factor identity resolution. Auto-match only when >= 2 of
        {name, DOB, phone} agree — no single signal is trusted (shared/caretaker
        phones overlap; names collide).

        Returns (patient_or_None, status, basis) where status is:
          matched | not_found | insufficient_info | ambiguous
        and basis names the agreeing identifiers (e.g. "name + DOB").
        """
        first = (first_name or "").strip().lower()
        last = (last_name or "").strip().lower()
        dob = str(date_of_birth) if date_of_birth else None
        nphone = _norm_phone(phone)

        has_name = bool(first and last)
        provided = sum([has_name, bool(dob), bool(nphone)])
        if provided < 2:
            return None, "insufficient_info", None

        matches: list[tuple[Patient, list[str]]] = []
        for p in self.patients:
            agree: list[str] = []
            if has_name and p.first_name.lower() == first and p.last_name.lower() == last:
                agree.append("name")
            if dob and str(p.date_of_birth) == dob:
                agree.append("DOB")
            if nphone and _norm_phone(p.phone) == nphone:
                agree.append("phone")
            if len(agree) >= 2:
                matches.append((p, agree))

        if len(matches) == 1:
            p, agree = matches[0]
            return p, "matched", " + ".join(agree)
        if len(matches) > 1:
            return None, "ambiguous", None
        return None, "not_found", None

    def match_patient(self, first_name, last_name, date_of_birth) -> Patient | None:
        """Convenience exact name+DOB match (used by deterministic tests)."""
        first = (first_name or "").strip().lower()
        last = (last_name or "").strip().lower()
        return next(
            (
                p
                for p in self.patients
                if p.first_name.lower() == first
                and p.last_name.lower() == last
                and str(p.date_of_birth) == str(date_of_birth)
            ),
            None,
        )


def load_messages() -> list[Message]:
    """Seeded inbound voicemails as `Message`s (annotation fields prefixed `_`
    are ignored — they document the intended demo scenario)."""
    messages: list[Message] = []
    for v in _load("voicemails.json"):
        messages.append(
            Message(
                id=v["id"],
                channel=Channel(v["channel"]),
                received_at=datetime.fromisoformat(v["received_at"].replace("Z", "+00:00")),
                raw_ref=v.get("raw_ref"),
                raw_body=v.get("raw_body"),
                transcript=v["transcript"],
            )
        )
    return messages
