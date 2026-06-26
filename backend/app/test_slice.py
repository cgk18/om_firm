"""End-to-end refill slice, offline (canned intents, seeded chart, no API):
  message -> intake -> orchestrator -> eligibility -> drafting -> Task queue.
Run:  python -m app.test_slice
"""

from __future__ import annotations

from app.contracts import default_policy
from app.eval.golden import canned_extract
from app.seed import REFERENCE_NOW, SeedStore, load_messages
from app.tasks import TasksRepo, apply_decision, intake_to_tasks

# Expected status lane per message.
EXPECT = {
    "vm_001": "ready", "vm_002": "needs_action", "vm_003": "needs_action",  # reschedule placeholder
    "vm_004": "needs_action", "vm_005": "urgent", "vm_006": "needs_action",
    "vm_007": "needs_action", "vm_008": "needs_action", "vm_010": "needs_action",
    "em_001": "ready", "vm_011": "ready", "vm_012": "needs_action", "vm_013": "ready",
    # vm_009 is multi-intent -> two tasks, checked separately.
}


def main() -> int:
    store, policy, repo = SeedStore(), default_policy(), TasksRepo()
    messages = {m.id: m for m in load_messages()}

    for m in messages.values():
        intake_to_tasks(m, repo=repo, store=store, policy=policy, now=REFERENCE_NOW, extract=canned_extract)

    by_msg: dict[str, list] = {}
    for t in repo.list():
        by_msg.setdefault(t.message_id, []).append(t)

    ok = True
    print(f"{'MSG':7} {'TYPE':10} {'STATUS':12} SUMMARY")
    print("=" * 92)
    for mid in messages:
        for t in by_msg.get(mid, []):
            print(f"{mid:7} {t.type.value:10} {t.status.value:12} {t.agent_summary}")
            for b in t.blockers:
                print(f"{'':30} ⚠ {b.label}")

    # Single-task expectations.
    for mid, want in EXPECT.items():
        got = by_msg.get(mid, [])
        if len(got) != 1 or got[0].status.value != want:
            ok = False
            print(f"  MISMATCH {mid}: expected 1 task {want}, got {[t.status.value for t in got]}")

    # Multi-intent: vm_009 -> refill ready + reschedule needs_action.
    nine = sorted((t.type.value, t.status.value) for t in by_msg.get("vm_009", []))
    if nine != [("refill", "ready"), ("reschedule", "needs_action")]:
        ok = False
        print(f"  MISMATCH vm_009 multi-intent: got {nine}")

    # Approve one ready task; confirm it flips to approved (no execution).
    ready = next(t for t in repo.list() if t.status.value == "ready")
    updated = apply_decision(repo, ready.id, "approve", reviewer="Riya")
    if updated.status.value != "approved" or updated.reviewed_by != "Riya":
        ok = False
        print("  MISMATCH approve flow")

    print("\nALL SLICE CHECKS PASS" if ok else "\nSLICE CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
