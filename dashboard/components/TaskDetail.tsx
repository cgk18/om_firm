"use client";

import { AlertTriangle, Mail, MousePointerClick, Voicemail } from "lucide-react";
import { fmtDateTime } from "@/lib/format";
import type { TaskView } from "@/lib/types";
import { StatusChip, TypeChip } from "./Chips";
import { PatientPanel } from "./PatientPanel";
import { ChecksPanel } from "./ChecksPanel";
import { DraftPanel } from "./DraftPanel";
import { DecisionBar } from "./DecisionBar";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</h3>
      {children}
    </section>
  );
}

export function TaskDetail({
  view,
  busy,
  onApprove,
  onDismiss,
  onReopen,
  onSaveEdit,
}: {
  view: TaskView | null;
  busy: boolean;
  onApprove: (note?: string) => void;
  onDismiss: (note?: string) => void;
  onReopen: () => void;
  onSaveEdit: (text: string) => void;
}) {
  if (!view) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-muted-foreground">
        <MousePointerClick className="size-7" aria-hidden />
        <p className="text-sm">Select a task from the queue to review it.</p>
      </div>
    );
  }

  const { task, transcript, patient, audio_url } = view;

  return (
    <div className="flex h-full flex-col">
      {/* header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-start justify-between gap-3">
          <h2 className="text-lg font-semibold tracking-tight text-foreground">{task.patient_name}</h2>
          <div className="flex shrink-0 items-center gap-2">
            <TypeChip type={task.type} />
            <StatusChip status={task.status} />
          </div>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{task.agent_summary}</p>
        {task.flagged_reason && (
          <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-accent">
            <AlertTriangle className="size-4" aria-hidden /> {task.flagged_reason}
          </p>
        )}
      </header>

      {/* scrollable body */}
      <div className="flex-1 space-y-6 overflow-y-auto px-6 py-5">
        <Section title="What the patient said">
          <div className="rounded-[--radius] border border-border bg-surface p-4">
            <p className="mb-2 flex items-center gap-1.5 text-xs text-muted-foreground">
              {audio_url ? (
                <>
                  <Voicemail className="size-3.5" aria-hidden /> Voicemail
                </>
              ) : (
                <>
                  <Mail className="size-3.5" aria-hidden /> Message
                </>
              )}
              <span aria-hidden>·</span>
              {fmtDateTime(task.created_at)}
            </p>
            {audio_url && (
              <audio controls src={`/api${audio_url}`} className="mb-3 w-full">
                <track kind="captions" />
              </audio>
            )}
            <blockquote className="border-l-2 border-border pl-3 text-sm italic text-foreground">
              {transcript ?? "No transcript available."}
            </blockquote>
          </div>
        </Section>

        <Section title="Patient context">
          <PatientPanel patient={patient} />
        </Section>

        {task.eligibility && task.eligibility.checks.length > 0 && (
          <Section title="Eligibility checks">
            <ChecksPanel eligibility={task.eligibility} />
          </Section>
        )}

        {task.blockers.length > 0 && (
          <Section title="Action needed before approving">
            <ul className="space-y-2">
              {task.blockers.map((b) => (
                <li
                  key={b.code}
                  className="rounded-[--radius-sm] border border-accent/30 bg-accent-soft px-3 py-2 text-sm"
                >
                  <span className="font-medium text-foreground">{b.label}</span>
                  {b.detail && <p className="mt-0.5 text-muted-foreground">{b.detail}</p>}
                </li>
              ))}
            </ul>
          </Section>
        )}

        <Section title="Drafted action">
          <DraftPanel task={task} busy={busy} onSaveEdit={onSaveEdit} />
        </Section>
      </div>

      {/* pinned decision bar */}
      <DecisionBar
        task={task}
        busy={busy}
        onApprove={onApprove}
        onDismiss={onDismiss}
        onReopen={onReopen}
      />
    </div>
  );
}
