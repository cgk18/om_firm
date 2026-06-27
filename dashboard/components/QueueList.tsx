"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Inbox } from "lucide-react";
import { LANE_META } from "@/lib/status";
import { ACTIVE_LANES, TERMINAL_LANES, groupByLane } from "@/lib/task-helpers";
import type { TaskStatus, TaskView } from "@/lib/types";
import { QueueRow } from "./QueueRow";

function LaneHeader({ lane, count }: { lane: TaskStatus; count: number }) {
  return (
    <div className="sticky top-0 z-10 flex items-center justify-between bg-background/95 px-4 py-2 backdrop-blur">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {LANE_META[lane].title}
      </h2>
      <span className="text-xs font-medium text-muted-foreground">{count}</span>
    </div>
  );
}

export function QueueList({
  views,
  selectedId,
  onSelect,
}: {
  views: TaskView[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const lanes = groupByLane(views);
  const [showDone, setShowDone] = useState(false);
  const doneCount = TERMINAL_LANES.reduce((n, l) => n + lanes[l].length, 0);
  const activeCount = ACTIVE_LANES.reduce((n, l) => n + lanes[l].length, 0);

  return (
    <div className="divide-y divide-border">
      {activeCount === 0 && (
        <div className="flex flex-col items-center gap-2 px-4 py-16 text-center text-muted-foreground">
          <Inbox className="size-6" aria-hidden />
          <p className="text-sm">Inbox zero — nothing waiting.</p>
        </div>
      )}

      {ACTIVE_LANES.map((lane) =>
        lanes[lane].length === 0 ? null : (
          <div key={lane}>
            <LaneHeader lane={lane} count={lanes[lane].length} />
            <div className="divide-y divide-border">
              {lanes[lane].map((v) => (
                <QueueRow
                  key={v.task.id}
                  view={v}
                  selected={v.task.id === selectedId}
                  onSelect={() => onSelect(v.task.id)}
                />
              ))}
            </div>
          </div>
        ),
      )}

      {doneCount > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowDone((s) => !s)}
            className="flex w-full items-center gap-1.5 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground hover:bg-surface-muted"
          >
            {showDone ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
            Done today
            <span className="ml-auto font-medium">{doneCount}</span>
          </button>
          {showDone && (
            <div className="divide-y divide-border">
              {TERMINAL_LANES.flatMap((l) => lanes[l]).map((v) => (
                <QueueRow
                  key={v.task.id}
                  view={v}
                  selected={v.task.id === selectedId}
                  onSelect={() => onSelect(v.task.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
