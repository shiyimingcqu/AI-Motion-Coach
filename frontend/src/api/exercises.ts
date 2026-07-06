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
