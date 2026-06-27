import { AlertTriangle } from "lucide-react";
import { QueueLane } from "@/components/QueueLane";
import { BackendUnavailableError, fetchTasks } from "@/lib/api";
import { APP_TAGLINE } from "@/lib/brand";
import { DONE_LANES, LANE_ORDER } from "@/lib/status";
import type { TaskStatus, TaskView } from "@/lib/types";

export const dynamic = "force-dynamic";

function group(views: TaskView[]): Record<TaskStatus, TaskView[]> {
  const out = {
    urgent: [],
    needs_action: [],
    ready: [],
    approved: [],
    dismissed: [],
  } as Record<TaskStatus, TaskView[]>;
  for (const v of views) out[v.task.status]?.push(v);
  return out;
}

export default async function QueuePage() {
  let views: TaskView[];
  try {
    views = await fetchTasks();
  } catch (e) {
    const msg =
      e instanceof BackendUnavailableError
        ? e.message
        : `Failed to load the queue: ${(e as Error).message}`;
    return (
      <div className="rounded-[--radius] border border-accent/30 bg-accent-soft px-4 py-3 text-sm text-foreground">
        <p className="flex items-center gap-2 font-medium text-accent">
          <AlertTriangle className="size-4" aria-hidden />
          Backend not reachable
        </p>
        <p className="mt-1 text-muted-foreground">{msg}</p>
      </div>
    );
  }

  const lanes = group(views);
  const doneCount = DONE_LANES.reduce((n, l) => n + lanes[l].length, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-foreground">Review queue</h1>
        <p className="text-sm text-muted-foreground">{APP_TAGLINE}</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {LANE_ORDER.map((lane) => (
          <QueueLane key={lane} lane={lane} views={lanes[lane]} />
        ))}
      </div>

      {doneCount > 0 && (
        <details className="rounded-[--radius] border border-border bg-surface px-4 py-3">
          <summary className="cursor-pointer text-sm font-medium text-muted-foreground">
            Done today · {doneCount}
          </summary>
          <div className="mt-4 grid grid-cols-1 gap-6 lg:grid-cols-2">
            {DONE_LANES.map((lane) => (
              <QueueLane key={lane} lane={lane} views={lanes[lane]} />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
