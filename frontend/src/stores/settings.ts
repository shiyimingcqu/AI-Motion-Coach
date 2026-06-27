import { defineStore } from "pinia";
import { reactive, watch } from "vue";

const STORAGE_KEY = "pose-evaluation-settings";

export type AppLanguage = "zh" | "en";
export type CameraResolution = "auto" | "1280x720" | "1920x1080" | "640x480";

export interface UserSettings {
  darkTrainingPanel: boolean;
  language: AppLanguage;
  notificationsEnabled: boolean;
  trainingCompleteReminder: boolean;
  cameraResolution: CameraResolution;
  cameraMirror: boolean;
}

export const LANGUAGE_OPTIONS: { value: AppLanguage; label: string }[] = [
  { value: "zh", label: "简体中文" },
  { value: "en", label: "English" }
];

export const CAMERA_RESOLUTION_OPTIONS: { value: CameraResolution; label: string }[] = [
  { value: "auto", label: "自动（推荐）" },
  { value: "1920x1080", label: "1920 × 1080" },
  { value: "1280x720", label: "1280 × 720" },
  { value: "640x480", label: "640 × 480" }
];

const defaultSettings: UserSettings = {
  darkTrainingPanel: false,
  language: "zh",
  notificationsEnabled: true,
  trainingCompleteReminder: false,
  cameraResolution: "auto",
  cameraMirror: true
};

function normalizeSettings(raw: Partial<UserSettings> & Record<string, unknown>): UserSettings {
  const language = raw.language === "en" ? "en" : "zh";
  const resolution = CAMERA_RESOLUTION_OPTIONS.some((item) => item.value === raw.cameraResolution)
    ? (raw.cameraResolution as CameraResolution)
    : defaultSettings.cameraResolution;

  return {
    darkTrainingPanel: Boolean(raw.darkTrainingPanel),
    language,
    notificationsEnabled: raw.notificationsEnabled !== false,
    trainingCompleteReminder: Boolean(raw.trainingCompleteReminder),
    cameraResolution: resolution,
    cameraMirror: raw.cameraMirror !== false
  };
}

function loadSettings(): UserSettings {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { ...defaultSettings };
  }

  try {
    const parsed = JSON.parse(raw) as Partial<UserSettings> & Record<string, unknown>;
    return normalizeSettings(parsed);
  } catch {
    return { ...defaultSettings };
  }
}

function syncThemeClass(enabled: boolean) {
  document.documentElement.classList.toggle("theme-dark", enabled);
}

function syncLanguageClass(language: AppLanguage) {
  document.documentElement.lang = language === "en" ? "en" : "zh-CN";
}

export const useSettingsStore = defineStore("settings", () => {
  const settings = reactive<UserSettings>(loadSettings());

  syncThemeClass(settings.darkTrainingPanel);
  syncLanguageClass(settings.language);

  watch(
    settings,
    (value) => {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
      syncThemeClass(value.darkTrainingPanel);
      syncLanguageClass(value.language);
    },
    { deep: true }
  );

  function resetSettings() {
    Object.assign(settings, defaultSettings);
  }

  function exportSettingsJson() {
    return JSON.stringify(settings, null, 2);
  }

  function importSettingsJson(_json: string) {
    return {
      ok: false,
      message: "导入功能开发中，敬请期待。"
    };
  }

  function resetToDefaults() {
    resetSettings();
    return {
      ok: true,
      message: "本地设置已恢复默认。"
    };
  }

  return {
    settings,
    resetSettings,
    exportSettingsJson,
    importSettingsJson,
    resetToDefaults
  };
});
