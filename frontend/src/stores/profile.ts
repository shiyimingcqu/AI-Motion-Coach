import { defineStore } from "pinia";
import { reactive, watch } from "vue";

const STORAGE_KEY = "pose-evaluation-profile";

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
  name: "林同学",
  occupation: "健身爱好者",
  height: "172",
  weight: "62",
  trainingGoal: "提升下肢稳定性与动作标准度",
  trainingPreferences: ["提高动作标准", "增强核心稳定", "改善体态"]
};

export function getDefaultAvatarText(name: string) {
  return name.trim().slice(0, 1) || "用";
}

export function shouldShowCustomAvatar(profile: UserProfile) {
  return profile.avatarMode === "custom" && Boolean(profile.avatarImage);
}

const LEGACY_OCCUPATION_MAP: Record<string, string> = {
  教练: "健身教练"
};

function normalizeProfile(
  raw: Partial<UserProfile> & {
    avatar?: string;
    studentId?: string;
    role?: string;
    stageGoals?: string[];
  }
): UserProfile {
  const legacyPreferences = Array.isArray(raw.trainingPreferences)
    ? raw.trainingPreferences
    : Array.isArray(raw.stageGoals)
      ? raw.stageGoals.filter((item) =>
          TRAINING_PREFERENCE_OPTIONS.includes(item as (typeof TRAINING_PREFERENCE_OPTIONS)[number])
        )
      : [...defaultProfile.trainingPreferences];
  const trainingPreferences =
    legacyPreferences.length > 0 ? legacyPreferences : [...defaultProfile.trainingPreferences];

  const avatarMode: AvatarMode =
    raw.avatarMode === "custom" || raw.avatarImage ? "custom" : "default";
  const rawOccupation = raw.occupation ?? raw.role ?? defaultProfile.occupation;
  const mappedOccupation = LEGACY_OCCUPATION_MAP[rawOccupation] ?? rawOccupation;

  return {
    avatarMode: raw.avatarMode ?? avatarMode,
    avatarImage: raw.avatarImage ?? "",
    name: raw.name ?? defaultProfile.name,
    occupation: OCCUPATION_OPTIONS.includes(mappedOccupation as (typeof OCCUPATION_OPTIONS)[number])
      ? mappedOccupation
      : defaultProfile.occupation,
    height: raw.height ?? defaultProfile.height,
    weight: raw.weight ?? defaultProfile.weight,
    trainingGoal: raw.trainingGoal ?? defaultProfile.trainingGoal,
    trainingPreferences
  };
}

function loadProfile(): UserProfile {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { ...defaultProfile, trainingPreferences: [...defaultProfile.trainingPreferences] };
  }

  try {
    return normalizeProfile(JSON.parse(raw));
  } catch {
    return { ...defaultProfile, trainingPreferences: [...defaultProfile.trainingPreferences] };
  }
}

export function setDefaultAvatar(profile: UserProfile) {
  profile.avatarMode = "default";
}

export function setCustomAvatar(profile: UserProfile, imageData: string) {
  profile.avatarImage = imageData;
  profile.avatarMode = "custom";
}

export const useProfileStore = defineStore("profile", () => {
  const profile = reactive<UserProfile>(loadProfile());

  watch(
    profile,
    (value) => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
      } catch {
        // localStorage 容量不足时由页面操作提示用户
      }
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
  }

  return { profile, useDefaultAvatar, useCustomAvatar, resetProfile };
});
