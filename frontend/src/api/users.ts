import { apiGet, apiPost, apiPut } from "./client";
import type { User } from "@/stores/auth";

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

export interface UpdateProfileRequest {
  nickname?: string;
}

export function updateProfile(data: UpdateProfileRequest) {
  return apiPut<User>("/auth/profile", data);
}

export function changePassword(old_password: string, new_password: string) {
  return apiPost<{ message: string }>("/auth/change-password", {
    old_password,
    new_password,
  });
}
