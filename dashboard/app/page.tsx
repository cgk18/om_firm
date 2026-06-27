import { AlertTriangle } from "lucide-react";
import { DashboardClient } from "@/components/DashboardClient";
import { BackendUnavailableError, fetchTasks } from "@/lib/api";
import type { TaskView } from "@/lib/types";

export const dynamic = "force-dynamic";

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
      <div className="p-6">
        <div className="rounded-[--radius] border border-accent/30 bg-accent-soft px-4 py-3 text-sm">
          <p className="flex items-center gap-2 font-medium text-accent">
            <AlertTriangle className="size-4" aria-hidden />
            Backend not reachable
          </p>
          <p className="mt-1 text-muted-foreground">{msg}</p>
        </div>
      </div>
    );
  }

  return <DashboardClient initialTasks={views} />;
}
