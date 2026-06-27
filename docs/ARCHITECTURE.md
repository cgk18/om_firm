# Otomeda — Architecture (v1)

## The flow (draft-and-route, no writeback)
```
Inbound message (voicemail audio | email | ...)
  → Transcribe (Deepgram STT for audio)
  → Intake: extract structured intent (patient, request type, details, urgency)
  → Eligibility / drafting agent per type:
       • prescription refill  → drafted refill action
       • reschedule           → proposed slot (draft)
       • escalation           → flag for human, no draft
  → Task created (status: ready | needs_action | urgent — by attention level)
  → Dashboard queue: staff sees message + read-only patient context + draft
  → Staff one-click APPROVE → status: approved (human executes in their own system)
       or DISMISS / EDIT the draft
```
No step writes to an EHR or sends a patient message automatically. Every
outbound (the refill, the booking, the patient SMS) is a **draft a human acts
on**.

## Current state (2026-06-25) — for the dashboard handoff

**Built & tested (backend, offline on seeded data):** intake (Claude Haiku,
prompt-and-parse) → orchestrator → eligibility → drafting → in-memory task queue,
with approve / dismiss / edit / reopen. All three task types (refill, reschedule,
message relay) and cross-cutting gates (emergency hard-stop, two-factor identity
match, patient-status gate, multi-intent → multiple tasks). 19 seeded scenarios,
all green via `app/test_slice.py`.

**Not built:** real audio transcription (Deepgram — runs off pre-filled / pasted
transcripts); the dashboard.

### What the dashboard consumes — the `Task` (see `backend/app/contracts/`)
- `id`, `message_id`, `patient_id`, `patient_name`
- `type`: `refill | reschedule | message_relay | escalate`
- `status` (the queue lanes): `ready` · `needs_action` · `urgent` · `approved` · `dismissed`
- `agent_summary` — one-line human summary
- `eligibility`: `{ eligible, checks: [{name, passed, detail}], flagged_reason }`
- `draft` (or null): `{ structured (Refill/Reschedule/MessageRelay action),
  rendered (the text staff read/edit/copy), confidence, editable }`
- `blockers`: `[{code, label, detail}]` — the "ACTION NEEDED" items (empty = ready)
- review fields: `created_at`, `reviewed_at`, `approved_at`, `rejected_at`,
  `reviewed_by`, `reviewer_note`

The **read-only patient-context card** is built from the seed store, not the Task:
`Patient` (name, DOB, phone, insurance, last_visit, status, primary provider) +
their active `Prescription`s + `Appointment`s. The **transcript** lives on the
`Message` (join via `task.message_id`).

### The API (built — `backend/app/main.py`, FastAPI)
Run: `cd backend && .venv/bin/uvicorn app.main:app --reload` (→ `localhost:8000`,
interactive docs at `/docs`). CORS open to all origins for the demo.
- `GET /tasks?status=&type=` → `list[TaskView]` — the queue, enriched.
- `GET /tasks/{id}` → `TaskView`.
- `POST /tasks/{id}/decision` `{decision: approve|dismiss|edit|reopen, note?, edited_text?, reviewer?}` → updated `TaskView`.
- `GET /patients/{id}` → `PatientCard`.
- `POST /ingest` `{transcript, channel}` → runs the **real Claude intake** on a
  pasted transcript and returns the new `TaskView`(s). The "watch the AI work"
  moment (needs `ANTHROPIC_API_KEY`).
- `POST /reset` → rebuilds the demo queue (handy between filming takes).

`TaskView` = `{ task, transcript, patient }` (see `app/api/schemas.py`). The queue
is **pre-seeded at startup** from the demo voicemails via the canned (offline)
extractor — full queue instantly, no key needed. All time math uses
`REFERENCE_NOW` (the demo's "today"). State is in-memory (single user); the repo
is behind an interface so a real DB drops in later.

## Carry-over map (from the public hackathon repo)
The hackathon repo (`Berkeley-AI-Hackathon`, public) is reference-only. We do
not import its code wholesale — we retype the parts worth keeping under the new
name. Buckets:

### KEEP — port the logic, retype clean
- `backend/api/intake/` — message → structured intent. Core IP.
- `backend/api/transcription/` — Deepgram STT.
- `backend/orchestrator/prescription_eligibility/` — refill eligibility logic.
- `backend/orchestrator/scheduling_eligibility/` — reschedule eligibility logic.
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

## What changed from the hackathon architecture
The hackathon flow had two ways to reach the outside world, **both
auto-executing**: an auto path (`Orchestrator → API action services → Action DB`,
no human) and an approval tail (`CHW approve → Execution queue → Auto execute →
External services`). v1 **amputates the entire execute half** and keeps the
listen→understand→check→draft half intact:
- **No auto path.** Every task hits the human review queue.
- **On approve → the task is marked `approved`; the human executes it in their
  own system.** No execution queue, no auto-execute, no external-service calls.
- **EHR / Records / Appointments → read-only seeded data** (simulates the Tier-2
  vision; never written to).
- **The "action" is a draft object**, not an executed side effect.
- **Audit / Action DB → task history** (no record of executed external actions).

(Message relay was originally parked but is now built — see Current state.)

## Module layout (as built)
```
backend/app/
  contracts/        # shared schemas: enums, message, intent, patient, draft, task, clinic_policy
  pipeline/
    intake.py         # Claude Haiku extraction (prompt-and-parse -> Intent)
    orchestrator.py   # linear spine: emergency -> identity -> status gate -> dispatch
  eligibility/        # refill.py, reschedule.py — deterministic, policy-driven checks
  drafting/           # refill.py, reschedule.py, relay.py — Draft + Blockers per type
  scheduling/         # holds.py — in-memory slot reservations
  tasks/              # repo.py (in-memory) + service.py (create / approve / dismiss / edit) — NO executor
  seed/               # seeded "EHR" JSON (patients, prescriptions, appointments, providers,
                      #   drug_conflicts, holidays) + demo voicemails
  eval/               # golden intents + scorer + model eval runner
  test_slice.py       # end-to-end: 19 messages -> task queue
dashboard/            # NOT BUILT YET — Next.js queue + history + read-only patient card
```
Not built: `transcription.py` (Deepgram) — the pipeline runs off pre-filled /
pasted transcripts; wire real audio later. The API IS built (`app/main.py`, see
Current state above).

## Data model direction (v1)
Centered on the message/task, not patient records:
- `message` — raw inbound (audio url / email body), channel, transcript, STT meta.
- `task` — type, status (**attention level**: ready / needs_action / urgent /
  approved / dismissed), extracted intent, eligibility result, the **draft**,
  flagged_reason, review fields, links to patient + message.
- `draft` — the heart of the pivot. A proposed action is ALWAYS present (we draft
  for everything); when eligibility isn't met, blockers say what to do first.
    - `structured` — machine fields (med, dosage, provider, slot…). The payload a
      future Tier-2 EHR integration would push on one click.
    - `rendered` — human-readable text the CHW reads / edits / copies into their
      own system today, with no integration.
    - `blockers[]` — ACTION NEEDED prerequisites (failed eligibility checks
      re-phrased as imperative next steps, e.g. "Schedule an appointment"). Empty
      = ready to approve. Each has a `code` the dashboard can wire an action to.
    - plus `confidence`, `editable`. One object is Tier-1-useful and Tier-2-ready.
- `patient` (seeded "EHR") — name, DOB, phone, last visit, active meds, insurance.
  Read-only; simulates the EHR for eligibility + the context card. No writeback.
- `ClinicPolicy` — per-clinic eligibility config (see below).

## LLM vs deterministic (resolved)
Principle: **the LLM understands and generates language; code decides.** Decisions
are deterministic so they stay auditable, explainable to a clinic, reproducible,
cheap, and configurable. (Exact integration points firmed up as we build.)
- **LLM:** intake extraction; triage/urgency; (optionally, later) rendered draft
  prose.
- **Deterministic:** patient matching; eligibility gates; slot finding; structured
  draft assembly.
- **Hybrid:** emergency detection = LLM (catches paraphrase like "can't catch my
  breath") + a keyword floor that always escalates — high recall, never miss.
- **v1 rendered draft = templates** (data is already structured; demo-safe).
  Revisit LLM-generated prose later.

## Orchestrator: linear (resolved)
v1 orchestrator is a linear, deterministic pipeline (route by request type via
if/else dispatch) — predictable, debuggable, demo-safe, and on-thesis (human in
control, not autonomous AI). Multi-intent voicemails are handled by looping over
the intake `requests[]` array (one task per request), not by an agent.

**When agentic might earn its place (later):** task types multiply past a handful
and branch logic gets unmaintainable; requests go open-ended in ways we can't
enumerate; (post-EHR, Tier 2) actions become multi-step real-world workflows
(prior auth, insurance back-and-forth) whose sequence varies per case — and only
with eval/guardrail infra to contain nondeterminism, **never in a live demo.**
Migration pattern: keep the trunk linear, let individual nodes (e.g. a drafting
sub-agent with tools) go agentic. **Agentic in the leaves, deterministic in the
trunk.**

## Eligibility config — ClinicPolicy (Level 1)
Eligibility checks read thresholds / lists / toggles from a per-clinic
`ClinicPolicy` object instead of hardcoded constants. Base rules are fixed; their
knobs are configurable. Ship a sensible **default policy**; clients can change
values (a strong sales moment — "set your own refill policy, no code").
```
ClinicPolicy (actual knobs):
  refill_recent_visit_days / refill_future_visit_window_days
  conflict_established_days / controlled_substance_excluded
  accepted_insurance: [...] / early_refill_buffer_days
  appointment_duration_minutes / default_working_hours
  reschedule_search_days / reschedule_far_out_days / reschedule_repeat_flag_threshold
```
**Level 1 only** — parameterize the rules we already have. **Not** a general rules
engine / client-authored rule types (Level 2 — deferred; that's the "complicates
it too much" zone). Every check takes `policy` as an argument from day one so this
is not a later retrofit.
> TODO (separate discussion): revisit the default rule *values* themselves — some
> current thresholds are up for change.

## Open research (before we ever promise writeback)
Map how the major EHRs actually expose data/actions: eClinicalWorks, Athena,
Epic/MyChart, etc. — API availability, cost, gating. This decides if/when
writeback is ever feasible. Do this together before committing to any
integration on a sales call.

## Stack (inherited, confirm on rebuild)
- Backend: Python / FastAPI.
- Dashboard: Next.js (App Router), Tailwind.
- Demo data: seeded fixtures (no live PHI).
