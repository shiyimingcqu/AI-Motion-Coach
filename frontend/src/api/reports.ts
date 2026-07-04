import { apiGet } from "./client";

export interface ReportItem {
  id: string;
  session_id: string;
  title: string;
  subtitle: string;
  type: string;
  date: string;
  exercise: string;
  exercise_name: string;
  exercises_count: number;
  sessions_count: number;
  average_score: number;
  calories: number;
  size: string;
  grade?: string;
  grade_label?: string;
  duration_minutes?: number;
  error_count?: number;
}

export interface ChartData {
  score_trend: { date: string; score: number }[];
  score_trend_by_exercise?: { exercise: string; name: string; trend: { date: string; score: number }[] }[];
  calorie_by_exercise: { name: string; value: number }[];
  exercise_distribution: { name: string; value: number }[];
  quality_radar: { dimensions: string[]; values: number[] };
  per_exercise_radar?: Record<string, { dimensions: string[]; values: number[] }>;
  error_by_exercise: { name: string; value: number }[];
}

export interface ExerciseComparisonItem {
  exercise: string;
  name: string;
  count: number;
  avg_score: number;
  calories: number;
  total_errors?: number;
  valid_rate?: number;
  best_score?: number;
  latest_score?: number;
  duration_minutes?: number;
}

export interface PersonalReport {
  average_score: number;
  total_sessions: number;
  total_duration_minutes: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  total_calories: number;
  trend: { date: string; score: number }[];
  exercise_breakdown: ExerciseComparisonItem[];
  exercise_comparison?: ExerciseComparisonItem[];
  exercise_trends?: { exercise: string; name: string; trend: { date: string; score: number }[] }[];
  feedback_summary?: { weaknesses: string[]; recommendations: string[] };
  recent_sessions: {
    session_id: string;
    exercise: string;
    score: number;
    calories?: number;
    created_at: string;
  }[];
  charts: ChartData;
}

export interface SessionEvaluation {
  grade: string;
  grade_label: string;
  exercise: string;
  exercise_name: string;
  dimension_scores: Record<string, number>;
  valid_rate: number;
  error_count: number;
  duration_minutes: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  summary: string;
}

export interface ReportDetail {
  session_id: string;
  exercise: string;
  exercise_name: string;
  created_at: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  calories_burned: number;
  evaluation: SessionEvaluation;
  charts: {
    quality_radar: { dimensions: string[]; values: number[] };
    rep_breakdown: { labels: string[]; values: number[] };
    score_gauge: { value: number; max: number };
  };
  report_item: ReportItem;
}

export interface ReportQuery {
  date_from?: string;
  date_to?: string;
  exercise?: string;
}

export function getReports(params?: ReportQuery) {
  const query = new URLSearchParams();
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  if (params?.exercise) query.set("exercise", params.exercise);
  const qs = query.toString();
  return apiGet<{ items: ReportItem[]; total: number }>(`/reports${qs ? `?${qs}` : ""}`);
}

export function getPersonalReport(params?: ReportQuery) {
  const query = new URLSearchParams();
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  if (params?.exercise) query.set("exercise", params.exercise);
  const qs = query.toString();
  return apiGet<PersonalReport>(`/reports/personal${qs ? `?${qs}` : ""}`);
}

export function getReportDetail(sessionId: string) {
  return apiGet<ReportDetail>(`/reports/${sessionId}`);
}

export async function exportReport(
  format: "pdf" | "csv",
  params?: ReportQuery,
): Promise<Blob> {
  const { useAuthStore } = await import("@/stores/auth");
  const authStore = useAuthStore();
  const query = new URLSearchParams();
  query.set("format", format);
  if (params?.date_from) query.set("date_from", params.date_from);
  if (params?.date_to) query.set("date_to", params.date_to);
  if (params?.exercise) query.set("exercise", params.exercise);

  const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
  const response = await fetch(`${API_BASE}/reports/export?${query.toString()}`, {
    headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {},
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `导出失败: ${response.status}`);
  }
  return response.blob();
}

export async function exportSessionReport(sessionId: string): Promise<Blob> {
  const { useAuthStore } = await import("@/stores/auth");
  const authStore = useAuthStore();
  const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";
  const response = await fetch(
    `${API_BASE}/reports/${sessionId}/export?format=pdf`,
    { headers: authStore.token ? { Authorization: `Bearer ${authStore.token}` } : {} },
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || `导出失败: ${response.status}`);
  }
  return response.blob();
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function downloadReport(blob: Blob, format: "pdf" | "csv") {
  const dateStr = new Date().toISOString().slice(0, 10);
  const ext = format === "pdf" ? "pdf" : "csv";
  downloadBlob(blob, `fitness_assessment_report_${dateStr}.${ext}`);
}

export function downloadSessionReport(blob: Blob, sessionId: string) {
  downloadBlob(blob, `training_report_${sessionId.slice(0, 8)}.pdf`);
}
