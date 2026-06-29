import { apiGet } from "./client";

export interface FeedbackItem {
  id: string;
  session_id: string;
  exercise: string;
  issue: string;
  severity: "high" | "medium" | "low";
  suggestion?: string;
  created_at: string;
}

export function getFeedbacks(params?: { session_id?: string; limit?: number }) {
  const query = new URLSearchParams();
  if (params?.session_id) query.set("session_id", params.session_id);
  if (params?.limit) query.set("limit", String(params.limit));
  const qs = query.toString();
  return apiGet<{ items: FeedbackItem[] }>(`/feedback${qs ? `?${qs}` : ""}`);
}
