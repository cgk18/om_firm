"""Deterministic check that each refill scenario lands where the spec says.
Runs offline (canned intents, seeded chart) — no API. Run:  python -m app.eligibility.test_refill_scenarios
"""

from __future__ import annotations

from app.contracts import default_policy
from app.eligibility import check_refill
from app.eval.golden import canned_extract
from app.seed import REFERENCE_NOW, SeedStore, load_messages

# Expected: (eligible?, the check expected to fail when not eligible)
EXPECT = {
    "vm_001": (True, None),                       # clean refill
    "vm_002": (False, "visit_requirement"),       # stale visit, no future appt
    "vm_004": (False, "insurance_accepted"),      # Oscar Health on file
    "vm_006": (False, "dosage_approved"),         # asks 80mg, script 40mg
    "vm_009": (True, None),                        # multi-intent: refill part is clean
    "vm_010": (False, "controlled_substance"),    # Alprazolam
    "vm_011": (True, None),                        # conflict established (>1yr)
    "vm_012": (False, "drug_conflict"),           # conflict fresh (<1yr)
    "vm_013": (True, None),                        # future appt saves the visit rule
    "em_001": (True, None),                        # email refill, clean
}


def main() -> int:
    store = SeedStore()
    policy = default_policy()
    messages = {m.id: m for m in load_messages()}

    ok = True
    for mid, (want_eligible, want_fail) in EXPECT.items():
        intent = canned_extract(messages[mid])
        patient = store.match_patient(intent.first_name, intent.last_name, intent.date_of_birth)
        # Use the refill request (primary for single-intent; first refill for multi).
        req = next((r for r in intent.requests if r.type.value == "refill"), intent.request)
        result = check_refill(request=req, patient=patient, store=store, policy=policy, now=REFERENCE_NOW)

        failed = [c.name for c in result.checks if not c.passed]
        good = result.eligible == want_eligible and (want_fail is None or want_fail in failed)
        ok = ok and good
        mark = "OK " if good else "XX "
        name = patient.full_name if patient else "(unmatched)"
        print(f"{mark}{mid} {name:14} eligible={result.eligible}  fails={failed or '-'}")
        if not good:
            print(f"     expected eligible={want_eligible}, fail in {want_fail}")
            for c in result.checks:
                print(f"       - {c.name}: {'pass' if c.passed else 'FAIL'} — {c.detail}")

    print("\nALL SCENARIOS PASS" if ok else "\nSOME SCENARIOS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
