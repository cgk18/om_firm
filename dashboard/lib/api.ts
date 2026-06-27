import "server-only";

import { BACKEND_BASE } from "./config";
import type { TaskView } from "./types";

export class BackendUnavailableError extends Error {}

/** Initial server-side fetch of the full enriched queue (used for first paint).
 *  Client-side reads/mutations go through the same-origin /api proxy routes. */
export async function fetchTasks(): Promise<TaskView[]> {
  let res: Response;
  try {
    res = await fetch(`${BACKEND_BASE}/tasks`, { cache: "no-store" });
  } catch {
    throw new BackendUnavailableError(
      `Could not reach the Otomeda API at ${BACKEND_BASE}. Start it with: cd backend && .venv/bin/uvicorn app.main:app --reload`,
    );
  }
  if (!res.ok) throw new Error(`GET /tasks failed (${res.status})`);
  return (await res.json()) as TaskView[];
}
