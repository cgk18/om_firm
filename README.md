# Otomeda

AI admin assistant for clinic front-desk staff. It listens to every inbound
patient message (voicemail first; email and other channels through the same
pipeline), figures out what the patient needs, and **drafts the action** — so
staff review and approve instead of starting from scratch. A human stays in
control of every decision.

> Repo working name `om_firm`. Product brand name: **Otomeda**.

## Docs
- [Product](docs/PRODUCT.md) — what, who, positioning, v1 scope.
- [Architecture](docs/ARCHITECTURE.md) — flow, data model, carry-over map.
- [Decisions](docs/DECISIONS.md) — decisions log + rationale.

## Status
**Backend pipeline + demo API built and tested; dashboard not started.**
Message → intake (Claude Haiku) → orchestrator → eligibility → drafting → task
queue, with a FastAPI layer the dashboard consumes. All three task types
(refill, reschedule, message relay) plus cross-cutting gates (emergency,
two-factor identity, patient status). 19 seeded demo scenarios (→ 20 tasks),
all green; live `POST /ingest` runs real Claude on a pasted transcript.

Next: the Next.js dashboard. See
[ARCHITECTURE.md → Current state](docs/ARCHITECTURE.md#current-state-2026-06-25--for-the-dashboard-handoff)
for the API + `TaskView` contract.

## Run the API
```
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload      # localhost:8000, docs at /docs
```

## Run the backend tests
```
cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m app.test_slice                       # message -> task queue, all scenarios
.venv/bin/python -m app.eligibility.test_refill_scenarios
.venv/bin/python -m app.eval.run --offline               # intake golden coverage
```
(The model eval — `app.eval.run` without `--offline` — needs `ANTHROPIC_API_KEY`.)
