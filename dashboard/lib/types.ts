// TypeScript mirror of the backend API contract. Source of truth lives in
// `backend/app/contracts/` (Task, Draft, Blocker, …) and `backend/app/api/
// schemas.py` (TaskView, PatientCard). Keep these in sync with those files.

/** What the orchestrator routed the task to. Mirrors enums.TaskType. */
export type TaskType = "refill" | "reschedule" | "message_relay" | "escalate";

/** Attention-level lane. Mirrors enums.TaskStatus. */
export type TaskStatus =
  | "ready" // drafted, all checks pass — one-click approve
  | "needs_action" // blocked — blockers must clear first
  | "urgent" // emergency / safety — jump the queue
  | "approved" // human approved; they execute in their own system
  | "dismissed"; // rejected / no action needed

export type RequestType = "refill" | "reschedule" | "message_relay" | "unknown";
export type Urgency = "routine" | "urgent" | "emergency" | "unknown";
export type TimeOfDay = "morning" | "afternoon" | "evening" | "anytime" | "unknown";

export interface PreferredTime {
  raw_text: string;
  date: string | null;
  start_time: string | null;
  time_of_day: TimeOfDay;
}

export interface ExtractedRequest {
  type: RequestType;
  details: string;
  orders: string[];
  preferred_times: PreferredTime[];
  urgency_signal: Urgency;
}

// --- Draft (the heart of draft-and-route) -----------------------------------

export interface RefillAction {
  type: "refill";
  patient_id: string;
  medication: string;
  dosage: string;
  instructions: string;
  provider_id: string | null;
}

export interface RescheduleAction {
  type: "reschedule";
  patient_id: string;
  provider_id: string | null;
  new_start: string;
  new_end: string;
  cancel_appointment_id: string | null;
}

export interface MessageRelayAction {
  type: "message_relay";
  patient_id: string;
  provider_id: string | null;
  message: string;
}

export type DraftAction = RefillAction | RescheduleAction | MessageRelayAction;

export interface Draft {
  structured: DraftAction;
  rendered: string;
  confidence: number;
  editable: boolean;
}

/** ACTION NEEDED prerequisite, re-phrased as an imperative next step. Lives on
 *  the Task (not the Draft). `code` is the machine handle the UI can wire to. */
export interface Blocker {
  code: string;
  label: string;
  detail: string;
}

export interface EligibilityCheck {
  name: string;
  passed: boolean;
  detail: string;
}

export interface EligibilityResult {
  eligible: boolean;
  checks: EligibilityCheck[];
  flagged_reason: string | null;
}

export interface Task {
  id: string;
  message_id: string;
  patient_id: string | null;
  patient_name: string;
  type: TaskType;
  status: TaskStatus;
  request: ExtractedRequest;
  agent_summary: string;
  eligibility: EligibilityResult | null;
  draft: Draft | null;
  blockers: Blocker[];
  flagged_reason: string | null;
  created_at: string;
  reviewed_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  reviewed_by: string | null;
  reviewer_note: string | null;
}

// --- Patient context card (read-only, from the seed store) ------------------

export interface MedView {
  medication_name: string;
  dosage: string;
  instructions: string;
}

export interface ApptView {
  start_time: string;
  provider_name: string | null;
  status: string;
}

export interface PatientCard {
  id: string;
  full_name: string;
  date_of_birth: string;
  phone: string | null;
  insurance_plan: string | null;
  last_visit: string | null;
  status: string;
  primary_provider: string | null;
  active_medications: MedView[];
  upcoming_appointments: ApptView[];
}

/** The enriched task the dashboard renders — one call per screen. */
export interface TaskView {
  task: Task;
  transcript: string | null;
  patient: PatientCard | null;
}

/** Staff decision verbs the API accepts (POST /tasks/{id}/decision). */
export type Decision = "approve" | "dismiss" | "edit" | "reopen";
