# {{NAME}} — Decisions Log

Running log of decisions + *why*, so we never re-litigate. Newest at top.

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
