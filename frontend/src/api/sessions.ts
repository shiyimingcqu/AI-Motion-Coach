import { apiDelete, apiGet, apiPost, apiPut } from "./client";

export interface FeedbackSummaryItem {
  issue: string;
  suggestion: string;
  severity: string;
  metric: string;
  value: number;
}

export interface SessionRecord {
  session_id: string;
  user_id: number | null;
  exercise: string;
  duration_seconds: number;
  total_count: number;
  valid_count: number;
  error_count: number;
  average_score: number;
  has_pose_replay?: boolean;
  created_at: string;
  feedback_summary?: string | null;
}

export interface PoseReplayLandmark {
  x: number;
  y: number;
  z: number;
  visibility?: number;
}

export interface PoseReplayFrame {
  timestamp_ms: number;
  landmarks: PoseReplayLandmark[];
}

export interface PoseReplaySegmentIssue {
  issue: string;
  suggestion: string;
  severity: string;
  metric: string;
  value: number;
}

export interface PoseReplaySegment {
  rep_index: number;
  start_frame_index: number;
  end_frame_index: number;
  start_timestamp_ms: number;
  end_timestamp_ms: number;
  score: number;
  issues: PoseReplaySegmentIssue[];
}

export interface PoseReplayNode {
  rep_index: number;
  frame_index: number;
  timestamp_ms?: number;
  start_frame_index?: number;
  score?: number;
  issues?: PoseReplaySegmentIssue[];
}

export interface PoseReplayMeta {
  schema_version?: number;
  source?: string;
  sample_interval_ms?: number;
  frame_count?: number;
  rep_segments?: PoseReplaySegment[];
  rep_nodes?: PoseReplayNode[];
}

export interface PoseReplayResponse {
  session_id: string;
  exercise: string;
  created_at: string | null;
  has_replay: boolean;
  meta: PoseReplayMeta | null;
  frames: PoseReplayFrame[];
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
  pose_replay?: PoseReplayFrame[];
  pose_replay_meta?: Record<string, unknown>;
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

export const LAST_SESSION_CACHE_KEY = "poseops:last-session";

export function cacheLastSessionForFeedback(session: SessionRecord) {
  sessionStorage.setItem(
    LAST_SESSION_CACHE_KEY,
    JSON.stringify({
      session_id: session.session_id,
      exercise: session.exercise,
      average_score: session.average_score,
      created_at: session.created_at,
      duration_seconds: session.duration_seconds,
    }),
  );
}

export function readLastSessionCache(sessionId?: string): SessionRecord | null {
  try {
    const raw = sessionStorage.getItem(LAST_SESSION_CACHE_KEY);
    if (!raw) return null;
    const cached = JSON.parse(raw) as SessionRecord;
    if (!cached?.session_id) return null;
    if (sessionId && cached.session_id !== sessionId) return null;
    return cached;
  } catch {
    return null;
  }
}

export function normalizeSessionSeed(raw: unknown): SessionRecord | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  const sessionId = record.session_id ?? record.id;
  if (typeof sessionId !== "string" || !sessionId) return null;
  return {
    session_id: sessionId,
    user_id: typeof record.user_id === "number" ? record.user_id : null,
    exercise: String(record.exercise ?? "squat"),
    duration_seconds: Number(record.duration_seconds ?? 0),
    total_count: Number(record.total_count ?? 0),
    valid_count: Number(record.valid_count ?? 0),
    error_count: Number(record.error_count ?? 0),
    average_score: Number(record.average_score ?? 0),
    created_at: String(record.created_at ?? new Date().toISOString()),
    has_pose_replay: Boolean(record.has_pose_replay),
    feedback_summary: typeof record.feedback_summary === "string" ? record.feedback_summary : null,
  };
}

export function getSessionReplay(session_id: string) {
  return apiGet<PoseReplayResponse>(`/sessions/${session_id}/replay`);
}

export function createSession(data: CreateSessionPayload) {
  return apiPost<SessionRecord>("/sessions", data);
}

export function updateSessionReplay(
  session_id: string,
  data: { pose_replay: PoseReplayFrame[]; pose_replay_meta?: Record<string, unknown> },
) {
  return apiPut<{ message: string; session_id: string; frame_count: number }>(
    `/sessions/${session_id}/replay`,
    data,
  );
}

export function deleteSession(session_id: string) {
  return apiDelete<{ message: string; session_id: string }>(`/sessions/${session_id}`);
}
