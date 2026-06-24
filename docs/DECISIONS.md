# {{NAME}} — Decisions Log

Running log of decisions + *why*, so we never re-litigate. Newest at top.

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
