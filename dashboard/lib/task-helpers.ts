// Pure derivations over a TaskView: queue ordering, lane grouping, and the
// context-aware labels the decision bar shows.

import type { Task, TaskStatus, TaskView } from "./types";

export const ACTIVE_LANES: TaskStatus[] = ["urgent", "needs_action", "ready"];
export const TERMINAL_LANES: TaskStatus[] = ["approved", "dismissed"];

export function isTerminal(status: TaskStatus): boolean {
  return status === "approved" || status === "dismissed";
}

/** Within a lane: oldest first (front desk works the backlog top-down). */
function byAge(a: TaskView, b: TaskView): number {
  return a.task.created_at.localeCompare(b.task.created_at);
}

export function groupByLane(views: TaskView[]): Record<TaskStatus, TaskView[]> {
  const out: Record<TaskStatus, TaskView[]> = {
    urgent: [],
    needs_action: [],
    ready: [],
    approved: [],
    dismissed: [],
  };
  for (const v of views) out[v.task.status]?.push(v);
  for (const lane of Object.keys(out) as TaskStatus[]) out[lane].sort(byAge);
  return out;
}

/** The primary approve-button copy — names what approval resolves, honestly
 *  (draft-and-route: approval marks the task approved; a human executes it). */
export function approveLabel(task: Task): string {
  switch (task.type) {
    case "refill":
      return "Approve refill draft";
    case "reschedule":
      return "Approve reschedule";
    case "message_relay":
      return "Approve & send to provider";
    case "escalate":
      return "Mark handled";
  }
}

/** A one-line, human description of the structured action approval represents. */
export function describeAction(task: Task): string {
  const d = task.draft?.structured;
  if (!d) return "Manual handling — no drafted action.";
  switch (d.type) {
    case "refill":
      return `Refill ${d.medication} ${d.dosage}`.trim();
    case "reschedule":
      return `Rebook to ${new Date(d.new_start).toLocaleString("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      })}`;
    case "message_relay":
      return "Relay message to the provider";
  }
}
