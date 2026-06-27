// Server-side base URL of the Otomeda FastAPI backend. The browser never talks
// to it directly — it goes through the same-origin proxy routes in app/api/*,
// which read this value.
export const BACKEND_BASE = (
  process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/$/, "");
