import { LANE_META } from "@/lib/status";
import type { TaskStatus, TaskView } from "@/lib/types";
import { TaskCard } from "./TaskCard";

export function QueueLane({ lane, views }: { lane: TaskStatus; views: TaskView[] }) {
  const meta = LANE_META[lane];
  return (
    <section className="space-y-3">
      <div className="flex items-baseline gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-foreground">{meta.title}</h2>
        <span className="rounded-full bg-surface-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {views.length}
        </span>
      </div>
      {meta.blurb && <p className="-mt-1 text-xs text-muted-foreground">{meta.blurb}</p>}
      {views.length === 0 ? (
        <p className="rounded-[--radius-sm] border border-dashed border-border px-3 py-6 text-center text-sm text-muted-foreground">
          {meta.emptyText}
        </p>
      ) : (
        <div className="space-y-3">
          {views.map((v) => (
            <TaskCard key={v.task.id} view={v} />
          ))}
        </div>
      )}
    </section>
  );
}
