import { apiDelete, apiGet, apiPost, apiPut } from "./client";

export interface ExerciseItem {
  id?: number;
  key: string;
  name: string;
  category: string;
  level: string;
  duration: string;
  description: string;
  modes: string[];
  errors: string[];
  accent: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ExerciseLibItem {
  key: string;
  name: string;
  description: string;
  supported_metrics: string[];
  core_angles?: string[];
  core_feature_keys?: string[];
}

export function getExerciseLibrary() {
  return apiGet<{ items: ExerciseItem[] }>("/exercises");
}

export function getSimpleExercises() {
  return apiGet<{ items: ExerciseLibItem[] }>("/exercises/simple");
}

export function createExercise(data: Partial<ExerciseItem>) {
  return apiPost<ExerciseItem>("/exercises", data);
}

export function updateExercise(key: string, data: Partial<ExerciseItem>) {
  return apiPut<ExerciseItem>(`/exercises/${key}`, data);
}

export function deleteExercise(key: string) {
  return apiDelete<{ message: string; key: string }>(`/exercises/${key}`);
}

export interface ActiveTemplate {
  template_id: string;
  action: string;
  name: string;
  view: string;
  version: string;
  valid_frames: number;
  source: string;
  is_enabled: boolean;
  has_video: boolean;
  has_pose_replay: boolean;
}

export interface TemplateReplayFrame {
  timestamp_ms: number;
  landmarks: Array<{ x: number; y: number; z: number; visibility?: number }>;
}

export interface TemplateReplayResponse {
  frames: TemplateReplayFrame[];
  total: number;
  session_id?: string;
  template_id?: string;
}

export function getActiveTemplate(exercise: string) {
  return apiGet<{ template: ActiveTemplate | null }>(`/exercises/${exercise}/templates/active`);
}

export function getTemplateReplay(template_id: string) {
  return apiGet<TemplateReplayResponse>(`/templates/${template_id}/replay`);
}

export async function getActiveTemplateReplay(exercise: string) {
  const res = await getActiveTemplate(exercise);
  if (!res.template) return null;
  const replay = await getTemplateReplay(res.template.template_id);
  return {
    template: res.template,
    frames: replay.frames.map((f) => ({
      timestamp_ms: f.timestamp_ms,
      landmarks: f.landmarks.map((lm) => ({
        x: lm.x,
        y: lm.y,
        z: lm.z ?? 0,
        visibility: lm.visibility ?? 1,
      })),
    })),
  };
}
