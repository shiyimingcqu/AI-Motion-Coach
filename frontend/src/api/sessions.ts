import { apiDelete, apiGet, apiPost } from "./client";

export interface SessionRecord {
  session_id: string;
  user_id: number | null;
  exercise: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  created_at: string;
  feedback_summary?: string | null;
}

export interface SessionsResponse {
  items: SessionRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionsQuery {
  limit?: number;
  offset?: number;
  exercise?: string;
  date_from?: string;
  date_to?: string;
}

export interface CreateSessionPayload {
  exercise: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  issues?: string[];
  suggestions?: string[];
}

export function getSessions(params?: SessionsQuery) {
  const query = new URLSearchParams();
  if (params?.limit) query.set("limit", String(params.limit));
  if (params?.offset) query.set("offset", String(params.offset));
  if (params?.exercise) query.set("exercise", params.exercise);
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  const qs = query.toString();
  return apiGet<SessionsResponse>(`/sessions${qs ? `?${qs}` : ""}`);
}

export function getSession(session_id: string) {
  return apiGet<SessionRecord>(`/sessions/${session_id}`);
}

export function createSession(data: CreateSessionPayload) {
  return apiPost<SessionRecord>("/sessions", data);
}

export function deleteSession(session_id: string) {
  return apiDelete<{ message: string; session_id: string }>(`/sessions/${session_id}`);
}
