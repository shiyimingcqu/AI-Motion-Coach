import { apiGet } from "./client";

export interface Exercise {
  key: string;
  name: string;
  description: string;
  supported_metrics: string[];
}

export function getExercises() {
  return apiGet<{ items: Exercise[] }>("/exercises");
}
