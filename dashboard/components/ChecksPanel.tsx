import { Check, X } from "lucide-react";
import type { EligibilityResult } from "@/lib/types";

export function ChecksPanel({ eligibility }: { eligibility: EligibilityResult }) {
  if (eligibility.checks.length === 0) return null;
  return (
    <ul className="space-y-1.5">
      {eligibility.checks.map((c, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          {c.passed ? (
            <Check className="mt-0.5 size-4 shrink-0 text-primary" aria-label="pass" />
          ) : (
            <X className="mt-0.5 size-4 shrink-0 text-urgent" aria-label="fail" />
          )}
          <span className="text-foreground">
            <span className="font-medium">{c.name}</span>
            {c.detail && <span className="text-muted-foreground"> — {c.detail}</span>}
          </span>
        </li>
      ))}
    </ul>
  );
}
