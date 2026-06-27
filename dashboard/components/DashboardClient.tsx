"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, RotateCcw } from "lucide-react";
import { decide, getTasks, resetDemo } from "@/lib/client";
import { ACTIVE_LANES, groupByLane } from "@/lib/task-helpers";
import { LANE_META } from "@/lib/status";
import type { Decision, TaskStatus, TaskView } from "@/lib/types";
import { QueueList } from "./QueueList";
import { TaskDetail } from "./TaskDetail";
import { Toast, type ToastState } from "./Toast";

const LANE_PILL: Record<TaskStatus, string> = {
  urgent: "text-urgent",
  needs_action: "text-accent",
  ready: "text-primary-deep",
  approved: "text-muted-foreground",
  dismissed: "text-muted-foreground",
};

export function DashboardClient({ initialTasks }: { initialTasks: TaskView[] }) {
  const [tasks, setTasks] = useState<TaskView[]>(initialTasks);
  const [selectedId, setSelectedId] = useState<string | null>(initialTasks[0]?.task.id ?? null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);

  const flash = useCallback((message: string, tone: ToastState["tone"] = "success") => {
    setToast({ message, tone });
    setTimeout(() => setToast(null), 2200);
  }, []);

  const selected = useMemo(
    () => tasks.find((t) => t.task.id === selectedId) ?? null,
    [tasks, selectedId],
  );

  const counts = useMemo(() => {
    const lanes = groupByLane(tasks);
    return (Object.keys(lanes) as TaskStatus[]).reduce(
      (acc, l) => ({ ...acc, [l]: lanes[l].length }),
      {} as Record<TaskStatus, number>,
    );
  }, [tasks]);

  const refresh = useCallback(async () => {
    try {
      setTasks(await getTasks());
    } catch {
      flash("Couldn't refresh the queue", "error");
    }
  }, [flash]);

  // Keep a selection sensible after the list changes.
  useEffect(() => {
    if (selectedId && tasks.some((t) => t.task.id === selectedId)) return;
    setSelectedId(tasks[0]?.task.id ?? null);
  }, [tasks, selectedId]);

  async function runDecision(decision: Decision, extra?: { note?: string; edited_text?: string }) {
    if (!selected) return;
    setBusy(true);
    try {
      const updated = await decide(selected.task.id, { decision, ...extra });
      setTasks((prev) => prev.map((t) => (t.task.id === updated.task.id ? updated : t)));
      const verb =
        decision === "approve"
          ? "Approved"
          : decision === "dismiss"
            ? "Dismissed"
            : decision === "reopen"
              ? "Reopened"
              : "Draft updated";
      flash(`${verb} — ${updated.task.patient_name}`);
    } catch (e) {
      flash((e as Error).message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function onReset() {
    setBusy(true);
    try {
      await resetDemo();
      await refresh();
      flash("Demo queue reset");
    } catch {
      flash("Reset failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* toolbar */}
      <div className="flex items-center gap-4 border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-3 text-sm">
          {ACTIVE_LANES.map((lane) => (
            <span key={lane} className="flex items-center gap-1.5">
              <span className={`font-semibold ${LANE_PILL[lane]}`}>{counts[lane]}</span>
              <span className="text-muted-foreground">{LANE_META[lane].title.toLowerCase()}</span>
            </span>
          ))}
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <button
            type="button"
            onClick={refresh}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-[--radius-sm] px-2.5 py-1.5 text-sm text-muted-foreground hover:bg-surface-muted disabled:opacity-40"
          >
            <RefreshCw className="size-4" /> Refresh
          </button>
          <button
            type="button"
            onClick={onReset}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-[--radius-sm] border border-border px-2.5 py-1.5 text-sm text-muted-foreground hover:bg-surface-muted disabled:opacity-40"
          >
            <RotateCcw className="size-4" /> Reset demo
          </button>
        </div>
      </div>

      {/* master / detail */}
      <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[360px_1fr]">
        <aside className="min-h-0 overflow-y-auto border-r border-border">
          <QueueList views={tasks} selectedId={selectedId} onSelect={setSelectedId} />
        </aside>
        <section className="min-h-0">
          <TaskDetail
            view={selected}
            busy={busy}
            onApprove={(note) => runDecision("approve", { note })}
            onDismiss={(note) => runDecision("dismiss", { note })}
            onReopen={() => runDecision("reopen")}
            onSaveEdit={(text) => runDecision("edit", { edited_text: text })}
          />
        </section>
      </div>

      <Toast toast={toast} />
    </div>
  );
}
