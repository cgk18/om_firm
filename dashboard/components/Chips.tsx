import { STATUS_META, TYPE_META } from "@/lib/status";
import type { TaskStatus, TaskType } from "@/lib/types";

export function StatusChip({ status }: { status: TaskStatus }) {
  const m = STATUS_META[status];
  const Icon = m.Icon;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${m.chip}`}
    >
      <Icon className="size-3.5" aria-hidden />
      {m.label}
    </span>
  );
}

export function TypeChip({ type }: { type: TaskType }) {
  const m = TYPE_META[type];
  const Icon = m.Icon;
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
      <Icon className="size-3.5" aria-hidden />
      {m.label}
    </span>
  );
}
