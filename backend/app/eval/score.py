"""Field-level scoring of an extracted Intent against the golden Intent."""

from __future__ import annotations

from app.contracts import Intent


def _ci(value: str | None) -> str | None:
    return value.strip().lower() if isinstance(value, str) else value


def _orders_set(req) -> set[str]:
    return {o.strip().lower() for o in req.orders}


def score_intent(got: Intent, want: Intent) -> dict[str, bool]:
    """Return a per-field pass/fail map. Only fields we can confidently grade."""
    checks: dict[str, bool] = {
        "first_name": _ci(got.first_name) == _ci(want.first_name),
        "last_name": _ci(got.last_name) == _ci(want.last_name),
        "date_of_birth": str(got.date_of_birth) == str(want.date_of_birth),
        "request_type": got.request.type == want.request.type,
        "orders": _orders_set(got.request) == _orders_set(want.request),
        "urgency": got.request.urgency_signal == want.request.urgency_signal,
        "num_requests": len(got.requests) == len(want.requests),
    }
    # Grade a resolved preferred date only where the golden expects one.
    want_dates = [pt.date for pt in want.request.preferred_times if pt.date]
    if want_dates:
        got_dates = [pt.date for pt in got.request.preferred_times if pt.date]
        checks["preferred_date"] = got_dates[:1] == want_dates[:1]
    return checks