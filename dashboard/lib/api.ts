import "server-only";

import type { Decision, PatientCard, TaskView } from "./types";

const BASE = (process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export class BackendUnavailableError extends Error {}

/** The full enriched queue (task + transcript + patient card per item). */
export async function fetchTasks(): Promise<TaskView[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/tasks`, { cache: "no-store" });
  } catch (e) {
    throw new BackendUnavailableError(
      `Could not reach the Otomeda API at ${BASE}. Is it running? (cd backend && .venv/bin/uvicorn app.main:app --reload)`,
    );
  }
  if (!res.ok) throw new Error(`GET /tasks failed (${res.status})`);
  return (await res.json()) as TaskView[];
}

export async function fetchTask(id: string): Promise<TaskView> {
  const res = await fetch(`${BASE}/tasks/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /tasks/${id} failed (${res.status})`);
  return (await res.json()) as TaskView;
}

export async function fetchPatient(id: string): Promise<PatientCard> {
  const res = await fetch(`${BASE}/patients/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /patients/${id} failed (${res.status})`);
  return (await res.json()) as PatientCard;
}

/** Apply a staff decision. Returns the updated, re-enriched task. */
export async function postDecision(
  id: string,
  body: { decision: Decision; note?: string; edited_text?: string; reviewer?: string },
): Promise<TaskView> {
  const res = await fetch(`${BASE}/tasks/${id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(detail.detail ?? `Decision failed (${res.status})`);
  }
  return (await res.json()) as TaskView;
}
