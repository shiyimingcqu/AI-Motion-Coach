import { apiGet } from "./client";

export interface ReportItem {
  id: string;
  title: string;
  subtitle: string;
  type: string;
  date: string;
  exercises_count: number;
  sessions_count: number;
  average_score: number;
  size: string;
}

export function getReports(params?: { date_from?: string; date_to?: string }) {
  const query = new URLSearchParams();
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  const qs = query.toString();
  return apiGet<{ items: ReportItem[] }>(`/reports${qs ? `?${qs}` : ""}`);
}

export interface DashboardStats {
  today_sessions: number;
  total_sessions: number;
  average_score: number;
  average_score_change: number;
  total_duration_minutes: number;
  recent_trend: { date: string; score: number }[];
  recent_sessions: { session_id: string; exercise: string; score: number; created_at: string }[];
}

export function getPersonalReport() {
  return apiGet<DashboardStats>("/reports/personal");
}
