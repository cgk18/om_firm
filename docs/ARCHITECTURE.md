# {{NAME}} — Architecture (v1)

## The flow (draft-and-route, no writeback)
```
Inbound message (voicemail audio | email | ...)
  → Transcribe (Deepgram STT for audio)
  → Intake: extract structured intent (patient, request type, details, urgency)
  → Eligibility / drafting agent per type:
       • prescription refill  → drafted refill action
       • reschedule           → proposed slot (draft)
       • escalation           → flag for human, no draft
  → Task created (status: needs_review)
  → Dashboard queue: staff sees message + read-only patient context + draft
  → Staff one-click APPROVE  → status: done (human executes in their own system)
       or REJECT / EDIT the draft
```
No step writes to an EHR or sends a patient message automatically. Every
outbound (the refill, the booking, the patient SMS) is a **draft a human acts
on**.

## Carry-over map (from the public hackathon repo)
The hackathon repo (`Berkeley-AI-Hackathon`, public) is reference-only. We do
not import its code wholesale — we retype the parts worth keeping under the new
name. Buckets:

### KEEP — port the logic, retype clean
- `backend/api/intake/` — message → structured intent. Core IP.
- `backend/api/transcription/` — Deepgram STT.
- `backend/api/prescription_eligibility/` — refill eligibility logic.
- `backend/api/scheduling_eligibility/` — reschedule eligibility logic.
- `backend/api/tasks/` (repo/service/router) — the unified task API + queue,
  **minus** the writeback dispatch.
- `backend/api/contracts/` — shared schemas / type backbone.
- dashboard `lib/{types,task,status}.ts` + the queue + history UI — the product
  surface and task model/presenters.

### REBUILD — capability needed, current code is a writeback shortcut
- `prescription_fulfillment/` → *generate a drafted refill action* (not fill).
- `scheduler/` → *propose a slot as a draft* (not auto-book).
- `confirmation/` → *draft a patient message* staff approve (not auto-send).
- `tasks/service.py` executor → rip out writeback dispatch; output drafts + route.
- Data layer / schema → reshape around `message → task → draft action`; drop
  EHR tables.

### PARK — out of v1, revisit later
- `message_relay/`, `summary/` (daily digest), `telephony/` (live phone ingest).

### DROP — no product role in draft-and-route
- `berkapp/` — the full eClinicalWorks EHR mock (~3,800 lines). It was "before"
  theater for the hackathon. **Exception:** lift its patient-panel layout when
  we build the small read-only context card. Stays in the public repo as
  reference for any future real-EHR work.

## Data model direction (v1)
Centered on the message/task, not patient records:
- `message` — raw inbound (audio url / email body), channel, transcript.
- `task` — type, status (needs_review / done / rejected / escalated), extracted
  intent, the **draft action**, links to patient + message.
- `patient` (seeded demo data) — minimal: name, DOB, last visit, active meds,
  insurance — enough for the read-only context card. No live EHR.

## Open research (before we ever promise writeback)
Map how the major EHRs actually expose data/actions: eClinicalWorks, Athena,
Epic/MyChart, etc. — API availability, cost, gating. This decides if/when
writeback is ever feasible. Do this together before committing to any
integration on a sales call.

## Stack (inherited, confirm on rebuild)
- Backend: Python / FastAPI.
- Dashboard: Next.js (App Router), Tailwind.
- Demo data: seeded fixtures (no live PHI).
