import {
  AlertOctagon,
  CalendarClock,
  CheckCircle2,
  CircleSlash,
  ClipboardCheck,
  MessageSquareText,
  Pill,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import type { TaskStatus, TaskType } from "./types";

// Status meaning is conveyed by icon + text + color together (never color alone).
export interface StatusMeta {
  label: string;
  Icon: LucideIcon;
  chip: string; // chip text/bg/border classes
  accent: string; // left accent border on the card
}

export const STATUS_META: Record<TaskStatus, StatusMeta> = {
  urgent: {
    label: "Urgent",
    Icon: AlertOctagon,
    chip: "text-urgent bg-urgent-soft border-urgent/30",
    accent: "border-l-urgent",
  },
  needs_action: {
    label: "Needs action",
    Icon: TriangleAlert,
    chip: "text-accent bg-accent-soft border-accent/30",
    accent: "border-l-accent",
  },
  ready: {
    label: "Ready to approve",
    Icon: CheckCircle2,
    chip: "text-primary-deep bg-primary-soft border-primary/30",
    accent: "border-l-primary",
  },
  approved: {
    label: "Approved",
    Icon: ClipboardCheck,
    chip: "text-muted-foreground bg-surface-muted border-border",
    accent: "border-l-border-strong",
  },
  dismissed: {
    label: "Dismissed",
    Icon: CircleSlash,
    chip: "text-muted-foreground bg-surface-muted border-border",
    accent: "border-l-border-strong",
  },
};

// The order lanes appear in the queue — most attention first.
export const LANE_ORDER: TaskStatus[] = ["urgent", "needs_action", "ready"];
export const DONE_LANES: TaskStatus[] = ["approved", "dismissed"];

export interface LaneMeta {
  title: string;
  blurb: string;
  emptyText: string;
}

export const LANE_META: Record<TaskStatus, LaneMeta> = {
  urgent: {
    title: "Urgent",
    blurb: "Emergency or safety signal — handle before anything else.",
    emptyText: "Nothing urgent.",
  },
  needs_action: {
    title: "Needs action",
    blurb: "Drafted, but something must be cleared before you can approve.",
    emptyText: "Nothing waiting on you.",
  },
  ready: {
    title: "Ready to approve",
    blurb: "Cleared every check — review the draft and approve.",
    emptyText: "Inbox zero — nothing ready.",
  },
  approved: { title: "Approved", blurb: "", emptyText: "Nothing approved yet." },
  dismissed: { title: "Dismissed", blurb: "", emptyText: "Nothing dismissed." },
};

export interface TypeMeta {
  label: string;
  Icon: LucideIcon;
}

export const TYPE_META: Record<TaskType, TypeMeta> = {
  refill: { label: "Refill", Icon: Pill },
  reschedule: { label: "Reschedule", Icon: CalendarClock },
  message_relay: { label: "Relay", Icon: MessageSquareText },
  escalate: { label: "Escalation", Icon: TriangleAlert },
};
