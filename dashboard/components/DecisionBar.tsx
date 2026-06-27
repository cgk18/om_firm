"use client";

import { useState } from "react";
import { Check, RotateCcw, X } from "lucide-react";
import { approveLabel } from "@/lib/task-helpers";
import type { Task } from "@/lib/types";

export function DecisionBar({
  task,
  busy,
  onApprove,
  onDismiss,
  onReopen,
}: {
  task: Task;
  busy: boolean;
  onApprove: (note?: string) => void;
  onDismiss: (note?: string) => void;
  onReopen: () => void;
}) {
  const [note, setNote] = useState("");
  const terminal = task.status === "approved" || task.status === "dismissed";

  if (terminal) {
    return (
      <div className="flex items-center justify-between gap-3 border-t border-border bg-surface px-5 py-3">
        <p className="text-sm text-muted-foreground">
          {task.status === "approved" ? "Approved" : "Dismissed"}
          {task.reviewed_by && ` by ${task.reviewed_by}`}
          {task.reviewer_note && <span className="italic"> — “{task.reviewer_note}”</span>}
        </p>
        <button
          type="button"
          disabled={busy}
          onClick={onReopen}
          className="inline-flex items-center gap-1.5 rounded-[--radius-sm] border border-border px-3 py-2 text-sm font-medium text-foreground hover:bg-surface-muted disabled:opacity-40"
        >
          <RotateCcw className="size-4" /> Reopen
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2 border-t border-border bg-surface px-5 py-3">
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Add a note (optional)…"
        className="w-full rounded-[--radius-sm] border border-border bg-surface-muted px-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none"
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => onApprove(note || undefined)}
          className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-[--radius-sm] bg-primary px-4 py-2.5 text-sm font-semibold text-on-primary hover:bg-primary-deep disabled:opacity-40"
        >
          <Check className="size-4" />
          {approveLabel(task)}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => onDismiss(note || undefined)}
          className="inline-flex items-center justify-center gap-1.5 rounded-[--radius-sm] border border-border px-4 py-2.5 text-sm font-medium text-foreground hover:bg-surface-muted disabled:opacity-40"
        >
          <X className="size-4" /> Dismiss
        </button>
      </div>
    </div>
  );
}
