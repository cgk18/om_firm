// Browser-side calls to the same-origin proxy routes (app/api/*).
import type { Decision, TaskView } from "./types";

export async function getTasks(): Promise<TaskView[]> {
  const res = await fetch("/api/tasks", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load the queue");
  return (await res.json()) as TaskView[];
}

export async function decide(
  id: string,
  body: { decision: Decision; note?: string; edited_text?: string },
): Promise<TaskView> {
  const res = await fetch(`/api/tasks/${id}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer: "Front desk", ...body }),
    cache: "no-store",
  });
  if (!res.ok) {
    const d = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(d.detail ?? "Action failed");
  }
  return (await res.json()) as TaskView;
}

export async function resetDemo(): Promise<{ tasks: number }> {
  const res = await fetch("/api/reset", { method: "POST", cache: "no-store" });
  if (!res.ok) throw new Error("Reset failed");
  return (await res.json()) as { tasks: number };
}
