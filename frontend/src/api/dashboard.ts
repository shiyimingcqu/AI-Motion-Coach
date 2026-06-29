import { apiGet } from "./client";

export interface DashboardStats {
  today_sessions: number;
  total_sessions: number;
  average_score: number;
  average_score_change: number;
  total_duration_minutes: number;
  recent_trend: { date: string; score: number }[];
  recent_sessions: {
    session_id: string;
    exercise: string;
    score: number;
    created_at: string;
  }[];
}

export function getDashboardStats() {
  return apiGet<DashboardStats>("/dashboard/stats");
}
