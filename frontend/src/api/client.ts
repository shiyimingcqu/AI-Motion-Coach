import { useAuthStore } from "@/stores/auth";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export function apiWebSocketUrl(path: string): string {
  const base = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;

  if (base.startsWith("http://") || base.startsWith("https://")) {
    return `${base.replace(/^http/, "ws")}${path}`;
  }

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}${base}${path}`;
}

function getAuthHeaders(): Record<string, string> {
  const authStore = useAuthStore();
  const headers: Record<string, string> = {};
  if (authStore.token) {
    headers["Authorization"] = `Bearer ${authStore.token}`;
  }
  return headers;
}

function handleUnauthorized(response: Response) {
  if (response.status === 401) {
    const authStore = useAuthStore();
    authStore.logout();
    window.location.href = "/login";
  }
}

async function throwRequestError(response: Response): Promise<never> {
  handleUnauthorized(response);
  const data = await response.json().catch(() => ({}));
  throw new Error(data.detail || `Request failed: ${response.status}`);
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
  return response.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
  return response.json();
}

export async function apiPatch<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
  return response.json();
}

export async function apiDelete(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
}

export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
  return response.json();
}
