"use client";

import { STATUS_META, TYPE_META } from "@/lib/status";
import { timeAgo } from "@/lib/format";
import type { TaskView } from "@/lib/types";

export function QueueRow({
  view,
  selected,
  onSelect,
}: {
  view: TaskView;
  selected: boolean;
  onSelect: () => void;
}) {
  const { task } = view;
  const status = STATUS_META[task.status];
  const type = TYPE_META[task.type];
  const TypeIcon = type.Icon;
  const StatusIcon = status.Icon;

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-current={selected}
      className={`w-full border-l-4 ${status.accent} px-4 py-3 text-left transition-colors ${
        selected ? "bg-primary-soft/60" : "bg-surface hover:bg-surface-muted"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate font-medium text-foreground">{task.patient_name}</span>
        <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(task.created_at)}</span>
      </div>
      <p className="mt-0.5 line-clamp-1 text-sm text-muted-foreground">{task.agent_summary}</p>
      <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <TypeIcon className="size-3.5" aria-hidden />
          {type.label}
        </span>
        <span aria-hidden>·</span>
        <span className="inline-flex items-center gap-1">
          <StatusIcon className="size-3.5" aria-hidden />
          {status.label}
        </span>
        {task.blockers.length > 0 && (
          <span className="ml-auto rounded-full bg-accent-soft px-1.5 py-0.5 font-medium text-accent">
            {task.blockers.length} to clear
          </span>
        )}
      </div>
    </button>
  );
}
