# {{NAME}} — Product

> Working name is a placeholder. Swap `{{NAME}}` everywhere once chosen.

## What it is
An AI admin assistant for clinic front-desk staff. It listens to every inbound
patient message (voicemail first; email and other channels through the same
pipeline), figures out what the patient needs, and **drafts the action** — so
staff review and approve instead of starting from scratch.

A human stays in control of every decision. We do not auto-execute anything
clinical.

## Who it's for
- **Market:** small, independent outpatient clinics — primary care, family
  medicine, internal medicine, pediatrics. < 20 providers.
- **Economic buyer / design target:** the office / practice manager (not the
  physician). The demo is built to impress *them*.
- Avoid initially: hospitals, academic medical centers, large health systems
  (slow procurement, heavy bureaucracy).

## Positioning
We sell **operational efficiency, not "AI."**

One-liner (provisional):
> Inbox-zero for the front desk: every patient message turned into a
> ready-to-send action.

Positioning statement:
> For small primary-care clinics drowning in patient voicemails and messages,
> {{NAME}} is an AI admin assistant that listens to every inbound message,
> figures out what the patient needs, and drafts the action — so staff just
> review and approve instead of starting from scratch. Unlike EHR add-ons or
> autonomous "AI agents," it keeps a human in control of every decision and
> works alongside the staff you already have.

### We ARE
- An operational-efficiency tool / copilot for *existing* staff.
- Draft-and-route: AI drafts, human approves and executes.
- Channel-agnostic intake (voicemail is the hero input).

### We are NOT
- Autonomous patient management.
- A staff replacement.
- An EHR.
- A clinical-decision maker.

## v1 scope
- **Goal: a polished demo**, architected as a straight line to a future pilot.
  No live PHI yet — demo runs on seeded data.
- **Draft-and-route only.** No EHR writeback. The "action" is a clean,
  ready-to-execute draft a human acts on in their own system.
- **Lead task types:** prescription refills + reschedules + message relay
  (un-parked during the build — see DECISIONS 2026-06-25). Escalation =
  kick-to-human path.
- **Channel-agnostic intake:** voicemail (Deepgram STT) as hero; email/other
  through the same parsing pipeline.
- **Read-only patient-context card** in the dashboard (name, DOB, last visit,
  active meds, insurance) from seeded demo data — gives the reviewer context to
  approve against. Read-only; nothing writes back.

## Explicitly out of v1
- EHR writeback / integration (needs per-vendor research first — see
  ARCHITECTURE.md "Open research").
- Auto-sending SMS/email to patients (becomes a *drafted* message staff approve).
- Live telephony ingestion (demo uses uploaded audio) + real audio transcription
  (pipeline currently runs on pre-filled transcripts).
- Daily summary digest; proactive "patient projected to run out" panel sweep.
- Real HIPAA/BAA posture (required before any pilot with live PHI, not for the
  demo).

## North star for next phase (post-demo)
This is a business-validation problem, not an engineering one. After the demo,
highest-leverage work is: land 3–5 pilot clinics → measure ROI (hours saved,
labor cost) → produce a case study. Feature expansion is secondary.
