import { apiDelete, apiGet, apiPut } from "./client";

export interface UserRecord {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export function getUsers() {
  return apiGet<{ items: UserRecord[] }>("/admin/users");
}

export function updateUser(id: number, data: Partial<Pick<UserRecord, "role" | "is_active">>) {
  return apiPut<UserRecord>(`/admin/users/${id}`, data);
}

export function deleteUser(id: number) {
  return apiDelete<{ message: string; user_id: number }>(`/admin/users/${id}`);
}

export function deleteTask(task_id: string) {
  return apiDelete<{ message: string; task_id: string }>(`/analysis/tasks/${task_id}`);
}
