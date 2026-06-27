"use client";

import { CheckCircle2, XCircle } from "lucide-react";

export interface ToastState {
  message: string;
  tone: "success" | "error";
}

export function Toast({ toast }: { toast: ToastState | null }) {
  if (!toast) return null;
  const ok = toast.tone === "success";
  return (
    <div className="pointer-events-none fixed bottom-5 left-1/2 z-50 -translate-x-1/2">
      <div
        className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium shadow-pop ${
          ok
            ? "border-primary/30 bg-surface text-primary-deep"
            : "border-urgent/30 bg-surface text-urgent"
        }`}
      >
        {ok ? <CheckCircle2 className="size-4" /> : <XCircle className="size-4" />}
        {toast.message}
      </div>
    </div>
  );
}
