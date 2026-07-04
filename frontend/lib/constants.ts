export const APP_NAME = "AI Research Assistant";
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const PLAN_LABELS = {
  free: "Free",
  pro: "Pro",
  team: "Team",
} as const;

export const PLAN_LIMITS = {
  free: { projects: 3, documents: 50 },
  pro: { projects: Infinity, documents: 1000 },
  team: { projects: Infinity, documents: Infinity },
} as const;

export const DOCUMENT_STATUS_POLL_INTERVAL_MS = 3000;
export const MAX_FILE_SIZE_MB = 25;
export const ACCEPTED_FILE_TYPES = ".pdf,.docx,.txt,.md,.markdown";
