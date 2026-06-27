# Otomeda — working instructions

Repo working name: `om_firm` (directory/remote). Product brand name: **Otomeda**.

## Read first
- `docs/PRODUCT.md` — what we're building, for whom, positioning, v1 scope.
- `docs/ARCHITECTURE.md` — the draft-and-route flow, data model, carry-over map.
- `docs/DECISIONS.md` — decisions + *why*. Append here when we decide something;
  don't re-litigate what's logged.

## Hard constraints (do not violate without a logged decision)
- **Draft-and-route only. No EHR writeback.** Every outbound (refill, booking,
  patient message) is a *draft a human approves and executes in their own
  system*. Nothing auto-executes anything clinical.
- **Demo-first, no live PHI.** Runs on seeded demo data.
- **Sell operational efficiency, not "AI."** Human stays in control.

## Carry-over rule
The public hackathon repo (`../Berkeley-AI-Hackathon`) is **reference only**.
Do not import its code wholesale — retype the parts worth keeping (see the
carry-over map in `docs/ARCHITECTURE.md`). This keeps the rebuild clean and the
IP unambiguous.

## v1 lead scope
Refills + reschedules + message relay (relay un-parked during the build).
Escalation = kick-to-human. Channel-agnostic intake (voicemail hero + email same
pipeline). Read-only patient-context card in the dashboard from seeded data.

## Build state (2026-06-25)
Backend pipeline built & tested offline (intake → orchestrator → eligibility →
drafting → in-memory task queue), all three task types. No API or dashboard yet.
See `docs/ARCHITECTURE.md` → "Current state" for the Task contract + the thin API
the dashboard needs. `docs/DECISIONS.md` is the running rationale log — append to
it; don't re-litigate.
