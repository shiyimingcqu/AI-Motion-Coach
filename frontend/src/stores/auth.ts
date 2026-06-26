import { defineStore } from "pinia";
import { apiPost, apiGet } from "@/api/client";

export interface User {
  id: number;
  username: string;
  role: "user" | "admin";
  is_active: boolean;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

const TOKEN_KEY = "pose_auth_token";

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    token: localStorage.getItem(TOKEN_KEY),
    user: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token && !!state.user,
    isAdmin: (state): boolean => state.user?.role === "admin",
    username: (state): string => state.user?.username ?? "",
  },

  actions: {
    setToken(token: string | null) {
      this.token = token;
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    },

    clearAuth() {
      this.token = null;
      this.user = null;
      this.error = null;
      localStorage.removeItem(TOKEN_KEY);
    },

    async login(username: string, password: string): Promise<User> {
      this.isLoading = true;
      this.error = null;

      try {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);

        const response = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData.toString(),
        });

        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.detail || "登录失败");
        }

        const data = await response.json();
        this.setToken(data.access_token);
        this.user = data.user;
        return data.user;
      } catch (err: any) {
        this.error = err.message || "登录失败";
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    async register(username: string, password: string, role: "user" | "admin" = "user"): Promise<User> {
      this.isLoading = true;
      this.error = null;

      try {
        const user = await apiPost<User>("/auth/register", {
          username,
          password,
          role,
        });
        return user;
      } catch (err: any) {
        this.error = err.message || "注册失败";
        throw err;
      } finally {
        this.isLoading = false;
      }
    },

    async fetchCurrentUser(): Promise<User | null> {
      if (!this.token) {
        this.user = null;
        return null;
      }

      this.isLoading = true;
      try {
        const user = await apiGet<User>("/auth/me");
        this.user = user;
        return user;
      } catch (err: any) {
        this.clearAuth();
        return null;
      } finally {
        this.isLoading = false;
      }
    },

    logout() {
      this.clearAuth();
    },
  },
});
