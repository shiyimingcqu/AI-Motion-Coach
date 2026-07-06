import { defineStore, storeToRefs } from "pinia";
import { reactive, watch } from "vue";
import { useAuthStore } from "./auth";

const STORAGE_KEY_PREFIX = "pose-evaluation-profile";
const AUTH_TOKEN_KEY = "pose_auth_token";

export const TRAINING_PREFERENCE_OPTIONS = [
  "增肌塑形",
  "减脂燃脂",
  "提升力量",
  "改善体态",
  "增强核心稳定",
  "提高动作标准",
  "提升柔韧性",
  "运动耐力强化",
  "康复与恢复",
  "日常健康维护"
] as const;

export const OCCUPATION_OPTIONS = [
  "健身爱好者",
  "公司职员",
  "学生",
  "教师",
  "医生",
  "工程师",
  "设计师",
  "运动员",
  "健身教练",
  "自由职业",
  "创业者",
  "退休人员",
  "其他"
] as const;

export type AvatarMode = "default" | "custom";

export interface UserProfile {
  avatarMode: AvatarMode;
  avatarImage: string;
  name: string;
  occupation: string;
  height: string;
  weight: string;
  trainingGoal: string;
  trainingPreferences: string[];
}

const defaultProfile: UserProfile = {
  avatarMode: "default",
  avatarImage: "",
  name: "",
  occupation: "健身爱好者",
  height: "0",
  weight: "0",
  trainingGoal: "",
  trainingPreferences: ["增肌塑形"]
};

export function getDefaultAvatarText(name: string) {
  return name.trim().slice(0, 1) || "用";
}

export function shouldShowCustomAvatar(profile: UserProfile) {
  return profile.avatarMode === "custom" && Boolean(profile.avatarImage);
}

function storageKey(): string {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return STORAGE_KEY_PREFIX;
  return STORAGE_KEY_PREFIX + "-" + token.slice(0, 8);
}

function loadFromLocalStorage(): UserProfile | null {
  try {
    const raw = localStorage.getItem(storageKey());
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") return parsed as UserProfile;
  } catch { /* ignore */ }
  return null;
}

function saveToLocalStorage(profile: UserProfile) {
  try {
    localStorage.setItem(storageKey(), JSON.stringify(profile));
  } catch { /* ignore */ }
}

function clearLocalStorage() {
  localStorage.removeItem(storageKey());
}

async function fetchProfile(): Promise<UserProfile | null> {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return null;
  try {
    const res = await fetch("/api/auth/profile", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    const data = await res.json();
    return {
      avatarMode: data.avatar_mode || "default",
      avatarImage: data.avatar_image || "",
      name: data.nickname || data.username || "",
      occupation: data.occupation || defaultProfile.occupation,
      height: data.height || "",
      weight: data.weight || "",
      trainingGoal: data.training_goal || "",
      trainingPreferences: data.training_preferences
        ? JSON.parse(data.training_preferences)
        : [...defaultProfile.trainingPreferences],
    };
  } catch {
    return null;
  }
}

async function saveProfileToServer(profile: UserProfile) {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (!token) return;
  try {
    await fetch("/api/auth/profile", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        nickname: profile.name || null,
        avatar_mode: profile.avatarMode,
        avatar_image: profile.avatarImage || null,
        occupation: profile.occupation || null,
        height: profile.height || null,
        weight: profile.weight || null,
        training_goal: profile.trainingGoal || null,
        training_preferences: JSON.stringify(profile.trainingPreferences),
      }),
    });
  } catch { /* ignore */ }
}

let _saveTimer: ReturnType<typeof setTimeout> | null = null;
function debouncedSave(profile: UserProfile) {
  if (_saveTimer) clearTimeout(_saveTimer);
  _saveTimer = setTimeout(() => saveProfileToServer(profile), 800);
}

export function setDefaultAvatar(profile: UserProfile) {
  profile.avatarMode = "default";
  profile.avatarImage = "";
}

export function setCustomAvatar(profile: UserProfile, imageData: string) {
  profile.avatarImage = imageData;
  profile.avatarMode = "custom";
}

export const useProfileStore = defineStore("profile", () => {
  // 优先从 localStorage 加载（带 token 前缀，不同用户不串数据）
  const cached = loadFromLocalStorage();
  const profile = reactive<UserProfile>(
    cached || { ...defaultProfile, trainingPreferences: [...defaultProfile.trainingPreferences] }
  );

  // 异步从后端加载
  let _initialized = false;
  async function initFromServer() {
    if (_initialized) return;
    _initialized = true;
    const serverProfile = await fetchProfile();
    if (serverProfile) {
      Object.assign(profile, serverProfile);
      saveToLocalStorage(profile);
    }
  }
  initFromServer();

  // 监听 auth store 的 token 变化：切换账号时重新加载，退出时重置
  const authStore = useAuthStore();
  const { token: authToken } = storeToRefs(authStore);
  watch(authToken, (newToken, oldToken) => {
    if (newToken && newToken !== oldToken) {
      // 换了账号或首次登录，重新从后端拉取
      _initialized = false;
      initFromServer();
    } else if (!newToken && oldToken) {
      // 退出登录，重置为默认值
      Object.assign(profile, {
        ...defaultProfile,
        trainingPreferences: [...defaultProfile.trainingPreferences]
      });
      _initialized = false;
    }
  });

  // 监听变更：写 localStorage + debounce 写后端
  watch(
    profile,
    (value) => {
      saveToLocalStorage(value);
      debouncedSave(value);
    },
    { deep: true }
  );

  function useDefaultAvatar() {
    setDefaultAvatar(profile);
  }

  function useCustomAvatar(imageData: string) {
    setCustomAvatar(profile, imageData);
  }

  function resetProfile() {
    Object.assign(profile, {
      ...defaultProfile,
      trainingPreferences: [...defaultProfile.trainingPreferences]
    });
    clearLocalStorage();
  }

  return { profile, useDefaultAvatar, useCustomAvatar, resetProfile };
});
