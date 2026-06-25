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
  → Task created (status: ready | needs_action | urgent — by attention level)
  → Dashboard queue: staff sees message + read-only patient context + draft
  → Staff one-click APPROVE → status: approved (human executes in their own system)
       or DISMISS / EDIT the draft
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
- **Message relay parked** (v1 = refills + reschedules).
- **Audit / Action DB → task history** (no record of executed external actions).

## Module layout (v1 rebuild)
```
backend/app/
  contracts/        # shared schemas: message, task, draft, patient, clinic_policy
  pipeline/
    transcription.py  # Deepgram (retype)
    intake.py         # Claude extraction (retype the prompt)
    orchestrator.py   # linear route-by-type dispatch
    drafting/         # NEW — builds the draft (replaces auto-execute)
  eligibility/        # deterministic, policy-driven checks
  tasks/              # repo + service (create / approve / reject / edit) — NO executor
  seed/               # seeded "EHR" JSON + demo voicemails
dashboard/            # Next.js queue + history + read-only patient card
```

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
ClinicPolicy (example knobs):
  refill_visit_window_days        # e.g. 90 / 180 / 365
  accepted_insurance: [...]
  controlled_substance_excluded
  require_dosage_match
  reschedule_max_lead_days
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
