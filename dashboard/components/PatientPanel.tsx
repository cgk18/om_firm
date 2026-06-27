import { CalendarDays, Pill, ShieldAlert } from "lucide-react";
import { ageFromDob, fmtDate, fmtDateTime } from "@/lib/format";
import type { PatientCard } from "@/lib/types";

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium text-foreground">{value}</dd>
    </div>
  );
}

export function PatientPanel({ patient }: { patient: PatientCard | null }) {
  if (!patient) {
    return (
      <div className="flex items-center gap-2 rounded-[--radius-sm] border border-accent/30 bg-accent-soft px-3 py-2 text-sm text-foreground">
        <ShieldAlert className="size-4 shrink-0 text-accent" aria-hidden />
        No patient matched to a chart — verify identity before acting.
      </div>
    );
  }
  const age = ageFromDob(patient.date_of_birth);
  return (
    <div className="rounded-[--radius] border border-border bg-surface p-4">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-foreground">
          {patient.full_name}
          {age !== null && <span className="ml-2 text-sm font-normal text-muted-foreground">{age}y</span>}
        </h4>
        {patient.status !== "active" && (
          <span className="rounded-full bg-urgent-soft px-2 py-0.5 text-xs font-medium text-urgent">
            {patient.status}
          </span>
        )}
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3">
        <Field label="DOB" value={fmtDate(patient.date_of_birth)} />
        <Field label="Phone" value={patient.phone ?? "—"} />
        <Field label="Insurance" value={patient.insurance_plan ?? "—"} />
        <Field label="Last visit" value={fmtDate(patient.last_visit)} />
        <Field label="Primary provider" value={patient.primary_provider ?? "—"} />
      </dl>

      <div className="mt-4 border-t border-border pt-3">
        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          <Pill className="size-3.5" aria-hidden /> Active medications
        </p>
        {patient.active_medications.length === 0 ? (
          <p className="text-sm text-muted-foreground">None on file.</p>
        ) : (
          <ul className="space-y-1">
            {patient.active_medications.map((m, i) => (
              <li key={i} className="text-sm text-foreground">
                <span className="font-medium">{m.medication_name}</span> {m.dosage}
                {m.instructions && <span className="text-muted-foreground"> — {m.instructions}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>

      {patient.upcoming_appointments.length > 0 && (
        <div className="mt-4 border-t border-border pt-3">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <CalendarDays className="size-3.5" aria-hidden /> Upcoming appointments
          </p>
          <ul className="space-y-1">
            {patient.upcoming_appointments.map((a, i) => (
              <li key={i} className="text-sm text-foreground">
                {fmtDateTime(a.start_time)}
                {a.provider_name && <span className="text-muted-foreground"> · {a.provider_name}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
