import { Clock, User } from "lucide-react";
import { STATUS_META, TYPE_META } from "@/lib/status";
import type { TaskView } from "@/lib/types";

function shortTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** One reviewable task in the queue. Walking-skeleton level: it surfaces the
 *  draft + blockers (the product's hero), but decision actions are not wired
 *  yet — that's the next pass. */
export function TaskCard({ view }: { view: TaskView }) {
  const { task, patient } = view;
  const status = STATUS_META[task.status];
  const type = TYPE_META[task.type];
  const TypeIcon = type.Icon;
  const StatusIcon = status.Icon;

  return (
    <article
      className={`rounded-[--radius] border border-border border-l-4 ${status.accent} bg-surface p-4 shadow-card`}
    >
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <User className="size-4 shrink-0 text-muted-foreground" aria-hidden />
            <h3 className="truncate font-semibold text-foreground">{task.patient_name}</h3>
          </div>
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{task.agent_summary}</p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <span
            className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${status.chip}`}
          >
            <StatusIcon className="size-3.5" aria-hidden />
            {status.label}
          </span>
          <span className="inline-flex items-center gap-1 rounded-full border border-border bg-surface-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
            <TypeIcon className="size-3.5" aria-hidden />
            {type.label}
          </span>
        </div>
      </header>

      {task.blockers.length > 0 && (
        <div className="mt-3 rounded-[--radius-sm] border border-accent/30 bg-accent-soft px-3 py-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-accent">Action needed</p>
          <ul className="mt-1 space-y-1">
            {task.blockers.map((b) => (
              <li key={b.code} className="text-sm text-foreground">
                <span className="font-medium">{b.label}</span>
                {b.detail && <span className="text-muted-foreground"> — {b.detail}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {task.draft && (
        <pre className="mt-3 max-h-40 overflow-hidden whitespace-pre-wrap rounded-[--radius-sm] border border-border bg-surface-muted px-3 py-2 font-mono text-[13px] leading-relaxed text-foreground">
          {task.draft.rendered}
        </pre>
      )}

      <footer className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <Clock className="size-3.5" aria-hidden />
          {shortTime(task.created_at)}
        </span>
        {patient && (
          <span>
            DOB {patient.date_of_birth}
            {patient.status !== "active" && (
              <span className="ml-2 rounded bg-urgent-soft px-1.5 py-0.5 font-medium text-urgent">
                {patient.status}
              </span>
            )}
          </span>
        )}
      </footer>
    </article>
  );
}
