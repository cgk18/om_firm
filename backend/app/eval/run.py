"""Intake eval runner — pressure-tests models against the golden set.

  python -m app.eval.run                  # all models (needs ANTHROPIC_API_KEY)
  python -m app.eval.run --model claude-haiku-4-5
  python -m app.eval.run --offline        # validate golden + canned extractor, no API

Reports per-model field-level accuracy and approximate cost, so we pick the
cheapest model that clears the set.
"""

from __future__ import annotations

import argparse
import os
import sys

from app.eval.golden import GOLDEN, canned_extract
from app.eval.score import score_intent
from app.seed import load_messages

MODELS = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-8"]

# $ per 1M tokens (input, output) — for a rough cost-per-run estimate.
PRICING = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-opus-4-8": (5.0, 25.0),
}


def _run_offline() -> int:
    messages = {m.id: m for m in load_messages()}
    missing = [mid for mid in messages if mid not in GOLDEN]
    print(f"Golden coverage: {len(GOLDEN)}/{len(messages)} messages.")
    if missing:
        print("  MISSING golden for:", ", ".join(missing))
    # Exercise the canned extractor + scorer (should be a perfect self-match).
    total = passed = 0
    for mid, msg in messages.items():
        if mid not in GOLDEN:
            continue
        checks = score_intent(canned_extract(msg), GOLDEN[mid])
        total += len(checks)
        passed += sum(checks.values())
    print(f"Canned extractor self-check: {passed}/{total} field checks pass (expected: all).")
    print("\nSet ANTHROPIC_API_KEY and run without --offline to score the models.")
    return 0


def _run_models(models: list[str]) -> int:
    from app.pipeline.intake import extract_intent

    import anthropic

    # Bounded so a hiccup fails fast instead of wedging the run.
    client = anthropic.Anthropic(timeout=60.0, max_retries=1)
    messages = [m for m in load_messages() if m.id in GOLDEN]

    # Rough per-call token estimate (system prompt is prompt-cached, so input is
    # small): ~200 input + ~400 output. Directional price comparison only.
    EST_IN, EST_OUT = 200, 400

    for model in models:
        total = passed = 0
        failures: list[str] = []
        print(f"\n=== {model} ===")
        for msg in messages:
            try:
                got = extract_intent(msg, client=client, model=model)
            except Exception as exc:  # noqa: BLE001 - surface, keep going
                print(f"  {msg.id}: ERROR {exc}")
                failures.append(f"{msg.id}:error")
                continue
            checks = score_intent(got, GOLDEN[msg.id])
            total += len(checks)
            passed += sum(checks.values())
            bad = [k for k, ok in checks.items() if not ok]
            if bad:
                failures.append(f"{msg.id}: {', '.join(bad)}")
        acc = (passed / total * 100) if total else 0.0
        in_rate, out_rate = PRICING.get(model, (0.0, 0.0))
        est_per_call = (EST_IN * in_rate + EST_OUT * out_rate) / 1_000_000
        print(f"  accuracy: {passed}/{total} field checks ({acc:.1f}%)")
        print(f"  est. cost: ~${est_per_call:.5f}/msg  (~${est_per_call * 3000:.2f} / 3k msgs)")
        if failures:
            print("  misses:")
            for f in failures:
                print(f"    - {f}")
        else:
            print("  clean sweep.")
    print("\nPick the cheapest model that clears the set (Haiku < Sonnet < Opus).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pressure-test intake models against the golden set.")
    parser.add_argument("--model", help="Run a single model instead of all three.")
    parser.add_argument("--offline", action="store_true", help="Validate golden + canned extractor, no API calls.")
    args = parser.parse_args(argv)

    # Load .env (repo root) so ANTHROPIC_API_KEY is available without manual sourcing.
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True))
    except ImportError:
        pass

    if args.offline:
        return _run_offline()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set — running --offline checks instead.\n")
        return _run_offline()

    models = [args.model] if args.model else MODELS
    return _run_models(models)


if __name__ == "__main__":
    raise SystemExit(main())
