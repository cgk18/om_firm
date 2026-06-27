"use client";

import { useEffect, useState } from "react";
import { Check, Copy, FileText, Pencil } from "lucide-react";
import { describeAction } from "@/lib/task-helpers";
import type { Task } from "@/lib/types";

export function DraftPanel({
  task,
  busy,
  onSaveEdit,
}: {
  task: Task;
  busy: boolean;
  onSaveEdit: (text: string) => void;
}) {
  const draft = task.draft;
  const [text, setText] = useState(draft?.rendered ?? "");
  const [editing, setEditing] = useState(false);
  const [copied, setCopied] = useState(false);

  // Reset local edit state whenever a different task / fresh draft arrives.
  useEffect(() => {
    setText(draft?.rendered ?? "");
    setEditing(false);
  }, [task.id, draft?.rendered]);

  if (!draft) {
    return (
      <p className="rounded-[--radius-sm] border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">
        No drafted action — this task is handled manually.
      </p>
    );
  }

  const dirty = text !== draft.rendered;

  async function copy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="rounded-[--radius] border border-border bg-surface">
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <span className="flex items-center gap-1.5 text-sm font-medium text-foreground">
          <FileText className="size-4 text-primary" aria-hidden />
          {describeAction(task)}
        </span>
        <div className="flex items-center gap-1">
          {draft.confidence < 1 && (
            <span className="mr-1 rounded-full bg-surface-muted px-2 py-0.5 text-xs text-muted-foreground">
              {Math.round(draft.confidence * 100)}% conf.
            </span>
          )}
          <button
            type="button"
            onClick={copy}
            className="inline-flex items-center gap-1 rounded-[--radius-sm] px-2 py-1 text-xs text-muted-foreground hover:bg-surface-muted"
          >
            {copied ? <Check className="size-3.5 text-primary" /> : <Copy className="size-3.5" />}
            {copied ? "Copied" : "Copy"}
          </button>
          {draft.editable && !editing && (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="inline-flex items-center gap-1 rounded-[--radius-sm] px-2 py-1 text-xs text-muted-foreground hover:bg-surface-muted"
            >
              <Pencil className="size-3.5" /> Edit
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="p-3">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={Math.max(6, text.split("\n").length + 1)}
            className="w-full resize-y rounded-[--radius-sm] border border-border bg-surface-muted p-3 font-mono text-[13px] leading-relaxed text-foreground focus:border-primary focus:outline-none"
          />
          <div className="mt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => {
                setText(draft.rendered);
                setEditing(false);
              }}
              className="rounded-[--radius-sm] px-3 py-1.5 text-sm text-muted-foreground hover:bg-surface-muted"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!dirty || busy}
              onClick={() => onSaveEdit(text)}
              className="rounded-[--radius-sm] bg-primary px-3 py-1.5 text-sm font-medium text-on-primary disabled:opacity-40"
            >
              Save edit
            </button>
          </div>
        </div>
      ) : (
        <pre className="whitespace-pre-wrap px-3 py-3 font-mono text-[13px] leading-relaxed text-foreground">
          {text}
        </pre>
      )}
    </div>
  );
}
