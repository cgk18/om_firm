# {{NAME}} — Decisions Log

Running log of decisions + *why*, so we never re-litigate. Newest at top.

## 2026-06-25 — Draft shape + task status buckets
- **Decision (draft for everything):** every actionable task carries a **proposed
  action**, even when eligibility fails. A `Draft` holds `structured` + `rendered`
  **plus `blockers[]`** — "ACTION NEEDED" prerequisites (failed eligibility checks
  re-phrased as imperative next steps, e.g. refill with no recent visit →
  "Schedule an appointment"). Empty blockers = ready to approve. Blockers live on
  the Draft (the next-steps travel with the proposal); each has a `code` the
  dashboard can later wire to an action (e.g. a Schedule button).
  **Why:** never just refuse — tell staff exactly what unblocks the action.
- **Decision (status = attention level, 5 buckets):** because every task has a
  draft, status conveys *how much attention is needed*, not draft presence.
  Active: **ready** (passes all checks, one-click approve), **needs_action**
  (blocked — incl. ambiguous / no patient match), **urgent** (emergency/safety).
  Terminal: **approved** (human will execute in their own system), **dismissed**.
  The *why* lives in `flagged_reason` + blockers; status carries only the lane.
  Not splitting needs_action into fixable-vs-judgment for v1 (can add later).
  **Why:** three active lanes separate the genuinely different kinds of attention
  (rubber-stamp / do-work-first / drop-everything) without over-engineering.

## 2026-06-25 — PHI / model-hosting posture
- **Decision:** Demo runs on the Claude API with **seeded fake data** — no PHI,
  so no HIPAA exposure. Proceed; don't block on compliance for the demo.
- **At pilot (live PHI):** the primary path is a **BAA** (Business Associate
  Agreement) with Anthropic directly, or Claude via AWS Bedrock / GCP Vertex
  under their BAA. A BAA is a contractual fix to the data-flow concern and lets
  us keep Claude's quality. **Using Claude is NOT inherently a HIPAA violation.**
- **Local / self-hosted open LLM is a documented fallback**, not the default —
  reserved for a clinic that contractually refuses any third-party processing.
  Drawbacks: quality gap (date math, valid JSON), hosting/GPU ops, per-clinic
  on-prem deploys, engineering time away from the real bottleneck (sales).
  **Why:** every healthcare-AI company solves this with a BAA; local trades
  quality + ops cost for perimeter control we don't need yet.

## 2026-06-25 — Architecture review of the hackathon repo + v1 direction
Read the actual hackathon code (not just the carry-over map). Findings + calls:
- **The pipeline is already ~80% draft-and-route.** `orchestrator/main_loop.py`
  emits a `proposed_action` + status (`pending_approval` / `escalated`) — that
  *is* the draft. The only true writeback is the final executor
  (`tasks/service.py::_execute_approval`), which writes to `berkapp` (a **fake
  eCW mock we built**, not a real EHR) and sends real SMS via Twilio/TextBelt.
  So "writeback" was always to our own mock — reframing to draft-and-route is a
  small cut, not a rebuild.
- **The LLM does almost nothing today** — Claude is used only for intake
  extraction (a strong prompt; our best asset) and the daily summary. Emergency
  detection, eligibility, dosage match, and date resolution are all brittle
  heuristics (substring matches, regex). **Decision:** the LLM rework is the
  highest-leverage build — push reasoning (triage/urgency, eligibility over
  retrieved context, draft generation) into the model, keep deterministic
  backstops where safety demands (emergency = LLM biased-to-escalate *plus*
  keyword net).

- **Decision (two-tier product):** Demo focuses on **Tier 1** (no EHR): listen →
  extract → classify → draft → prioritize → queue; eligibility "smarts" need
  chart data we don't have without integration. **Tier 2** (with EHR read/write)
  is the vision: auto-verify against the chart + one-click push.
  **Why:** the verification intelligence *is* the EHR-dependent part; without it
  the defensible value is triage + drafting (kills the listening/typing/triage
  time), and that's honest and sellable.
- **Decision (demo eligibility):** keep a **seeded patient/prescription dataset
  that stands in for the EHR**, run the real auto-verification against it, and
  **narrate it honestly** as the Tier-2 vision ("with EHR read access this is
  automatic; without it you still get the draft + a what-to-verify checklist").
  **Why:** best demo wow without vaporware; the seed simulates integration so we
  can *show* Tier 2 while shipping Tier 1.
- **Decision (stack):** keep Python/FastAPI + Next.js/Tailwind. Explicitly **not
  Java** — switching discards the working intake pipeline and SDK ergonomics for
  zero demo benefit.
- **Decision (carry-over):** start fresh in `om_firm`; retype (not import) the
  keepers — intake prompt + schemas, Deepgram wrapper, task/status state machine
  + dashboard queue/history UI, eligibility *rules as reference*, demo audio +
  seeded fixtures. Leave behind `berkapp`, the writeback executor, Twilio/
  TextBelt auto-send, telephony, message_relay/summary.
- **Decision (first build):** scaffold repo + data model (FastAPI + Next
  skeleton, `message → task → draft` schema, seeded fixtures) before filling in
  agents.

## 2026-06-24 — Continuing the hackathon project solo
- **Decision:** The originator (group leader at the hackathon) continues the
  project solo. One former teammate already approached separately; the other two
  get a warm courtesy heads-up, no invitation.
  **Why:** Idea + leadership were the originator's; a hackathon weekend isn't
  co-founder equity. Clarity now is cheap; later it's a negotiation.

- **Decision:** Leave the public hackathon repo public + untouched (teammates'
  portfolios). Start a **new private repo** and **rebuild clean** under a new
  name. Do not import teammates' code wholesale.
  **Why:** Sidesteps IP entirely (not using their code, just the originator's
  idea + learnings). They keep their artifact. Rebuild was needed anyway for the
  draft-and-route / HIPAA-real direction.

- **Decision (name):** Deferred — originator will pick. Wants a fully invented,
  zero-index word (cf. their prior "foochastic"). Placeholder `{{NAME}}` until
  then.

## 2026-06-24 — v1 scope locked
- **Demo first**, not pilot. Architected toward a real pilot. No live PHI yet.
  **Why:** Pilot needs HIPAA/BAA + a willing clinic; demo de-risks and is the
  sales asset.
- **Draft-and-route, NO EHR writeback** in v1.
  **Why:** Real EHR write integration is per-vendor, expensive, gated — could
  eat months and isn't pilotable. Draft-and-route is faster, safer (no
  clinical-decision liability), and mostly already built. Writeback becomes a
  later premium add-on.
- **Lead types: refills + reschedules**; escalation = kick-to-human.
  **Why:** Narrow is more credible; these are the highest-volume routine asks.
  (May sanity-check with a couple of doctors.)
- **Channel-agnostic intake** (voicemail hero + email/others same pipeline).
  **Why:** The asset is "any inbound patient message → drafted action," not
  voicemail specifically. Also constrains naming away from voicemail-only words.
- **Read-only patient-context card** in the demo (seeded data), not the full
  berkapp EHR mock.
  **Why:** Gives the reviewer context to approve against; the full mock has no
  product role in draft-and-route. Crib its layout for the card.
- **Buyer = office/practice manager** at independent primary care, < 20
  providers. Design the demo to impress them. (Tentative pending doctor convos.)

## 2026-06-24 — Positioning
- Sell **operational efficiency, not "AI."** "We draft and route; a human
  decides and executes."
  **Why:** Healthcare buyers are conservative; the safe, human-in-control story
  sells faster and dodges liability. See PRODUCT.md for the full statement.

## Reminders for future planning
- Bottleneck after the demo is **market validation**, not engineering. Prioritize
  pilot acquisition, ROI measurement, case studies over new AI features.
- HIPAA/BAA is the gate for any *pilot* with live PHI — treat as Priority 0 when
  the demo converts to a pilot conversation.
