// Small pure formatting helpers shared across the UI.

// Demo "today" — matches the backend REFERENCE_NOW so ages/dates line up.
export const REFERENCE_NOW = new Date("2026-06-26T00:00:00Z");

export function ageFromDob(dob?: string | null): number | null {
  if (!dob) return null;
  const birth = new Date(dob);
  let age = REFERENCE_NOW.getUTCFullYear() - birth.getUTCFullYear();
  const m = REFERENCE_NOW.getUTCMonth() - birth.getUTCMonth();
  if (m < 0 || (m === 0 && REFERENCE_NOW.getUTCDate() < birth.getUTCDate())) age -= 1;
  return age;
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function fmtDateTime(iso?: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** Compact relative age of a timestamp, e.g. "3h ago". */
export function timeAgo(iso?: string | null): string {
  if (!iso) return "";
  const then = new Date(iso).getTime();
  const now = REFERENCE_NOW.getTime();
  const mins = Math.round((now - then) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return `${days}d ago`;
}
