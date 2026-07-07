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

export async function apiGet<T>(path: string, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: getAuthHeaders(),
      signal: controller.signal,
    });
    if (!response.ok) {
      await throwRequestError(response);
    }
    return response.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("请求超时，请确认后端服务已启动");
    }
    if (err instanceof TypeError) {
      throw new Error("无法连接后端服务器，请确认后端已启动");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
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

export async function apiPut<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
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

export async function apiDelete<T = void>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    await throwRequestError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export async function apiUpload<T>(path: string, formData: FormData, timeoutMs = 600000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
      signal: controller.signal,
    });
    if (!response.ok) {
      await throwRequestError(response);
    }
    return response.json();
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error("请求超时，视频分析耗时较长，请稍后重试或缩短视频长度");
    }
    if (err instanceof TypeError) {
      throw new Error("无法连接后端服务器，请确认后端已启动 (http://localhost:8000)");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}
