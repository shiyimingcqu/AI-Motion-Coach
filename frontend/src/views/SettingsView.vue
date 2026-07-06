<template>
  <div class="settings-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("settings.title") }}</h1>
        <p>{{ $t("settings.description") }}</p>
      </div>
      <button class="back-home-btn" type="button" @click="router.push('/')">
        返回首页
      </button>
    </header>

    <section class="settings-layout">
      <div class="settings-main">
        <!-- 个人资料 -->
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-blue"><User :size="22" /></span>
            <h2>{{ $t("settings.profile.title") }}</h2>
          </header>
          <StateDisplay v-if="profileLoading" type="loading" skeleton="text" />
          <template v-else>
            <label>
              {{ $t("settings.profile.username") }}
              <input :value="authStore.username" type="text" readonly class="readonly-input" />
            </label>
            <label>
              {{ $t("settings.profile.role") }}
              <input
                :value="authStore.isAdmin ? $t('settings.profile.roleAdmin') : $t('settings.profile.roleUser')"
                type="text"
                readonly
                class="readonly-input"
              />
            </label>
            <label>
              {{ $t("settings.profile.nickname") }}
              <input v-model="nickname" type="text" :placeholder="$t('settings.profile.nicknamePlaceholder')" />
            </label>
            <button
              class="outline-wide-button"
              type="button"
              :disabled="profileSaving"
              @click="saveProfile"
            >
              {{ profileSaving ? $t("settings.profile.saving") : $t("settings.profile.save") }}
            </button>
            <p v-if="profileMessage" class="settings-message" :class="profileMessageType">{{ profileMessage }}</p>
          </template>
        </article>

        <!-- 修改密码 -->
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-purple"><Lock :size="22" /></span>
            <h2>{{ $t("settings.password.title") }}</h2>
          </header>
          <label>
            {{ $t("settings.password.current") }}
            <input v-model="passwordForm.old" type="password" :placeholder="$t('settings.password.currentPlaceholder')" />
          </label>
          <label>
            {{ $t("settings.password.new") }}
            <input v-model="passwordForm.new1" type="password" :placeholder="$t('settings.password.newPlaceholder')" />
          </label>
          <label>
            {{ $t("settings.password.confirm") }}
            <input v-model="passwordForm.new2" type="password" :placeholder="$t('settings.password.confirmPlaceholder')" />
          </label>
          <button
            class="outline-wide-button"
            type="button"
            :disabled="passwordSaving"
            @click="changePassword"
          >
            {{ passwordSaving ? $t("settings.password.changing") : $t("settings.password.change") }}
          </button>
          <p v-if="passwordMessage" class="settings-message" :class="passwordMessageType">{{ passwordMessage }}</p>
        </article>

        <!-- 通知设置 -->
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-orange"><Bell :size="22" /></span>
            <h2>{{ $t("settings.notifications.title") }}</h2>
          </header>
          <label v-for="item in notificationKeys" :key="item" class="settings-toggle-row">
            <span>{{ $t(`settings.notifications.${item}`) }}</span>
            <input type="checkbox" :checked="item !== 'weeklyReports'" />
          </label>
        </article>

        <!-- 数据与存储 -->
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-green"><Database :size="22" /></span>
            <h2>{{ $t("settings.data.title") }}</h2>
          </header>
          <div class="storage-row">
            <span>{{ $t("settings.data.storageUsed") }}</span>
            <strong>{{ $t("settings.data.sessions", { count: totalSessions }) }} / {{ $t("settings.data.minutes", { count: totalMinutes }) }}</strong>
          </div>
          <label class="settings-check">
            <input type="checkbox" checked />
            {{ $t("settings.data.autoBackup") }}
          </label>
        </article>
      </div>

      <aside class="settings-side">
        <article class="settings-side-card blue-side-card">
          <span class="side-icon blue-solid"><Globe2 :size="26" /></span>
          <h2>{{ $t("common.language") }}</h2>
          <select v-model="currentLocale" @change="switchLanguage">
            <option value="en-US">{{ $t("common.english") }}</option>
            <option value="zh-CN">{{ $t("common.chinese") }}</option>
          </select>
        </article>

        <article class="settings-side-card purple-side-card">
          <span class="side-icon purple-solid"><Shield :size="26" /></span>
          <h2>{{ $t("common.privacy") }}</h2>
          <label><input type="checkbox" checked /> {{ $t("common.dataAnalytics") }}</label>
          <label><input type="checkbox" /> {{ $t("common.shareProgress") }}</label>
        </article>

        <article class="settings-side-card theme-side-card">
          <span class="side-icon theme-solid"><Sun :size="26" /></span>
          <h2>主题</h2>
          <select v-model="currentTheme" @change="switchTheme">
            <option v-for="opt in THEME_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </article>

        <article class="settings-side-card">
          <h2>{{ $t("common.systemInfo") }}</h2>
          <dl class="system-info-list">
            <div><dt>{{ $t("common.version") }}</dt><dd>v2.1.0</dd></div>
            <div><dt>{{ $t("common.lastUpdated") }}</dt><dd>{{ today }}</dd></div>
            <div><dt>{{ $t("common.aiModel") }}</dt><dd>PoseNet v4</dd></div>
          </dl>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { Bell, Database, Globe2, Lock, Shield, Sun, User } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import { useAuthStore } from "@/stores/auth";
import { useSettingsStore, THEME_OPTIONS, type ThemeMode } from "@/stores/settings";
import { getPersonalReport } from "@/api/reports";
import { updateProfile, changePassword as apiChangePassword } from "@/api/users";

const { t, locale } = useI18n();
const router = useRouter();
const authStore = useAuthStore();
const settingsStore = useSettingsStore();

const notificationKeys = ["trainingReminders", "achievementAlerts", "errorNotifications", "weeklyReports"];

const currentLocale = ref(locale.value);
const currentTheme = ref<ThemeMode>(settingsStore.settings.theme);

function switchLanguage() {
  locale.value = currentLocale.value;
  localStorage.setItem("locale", currentLocale.value);
}

function switchTheme() {
  settingsStore.settings.theme = currentTheme.value;
}

// Profile
const nickname = ref(authStore.username);
const profileLoading = ref(false);
const profileSaving = ref(false);
const profileMessage = ref("");
const profileMessageType = ref("");

// Password
const passwordForm = ref({ old: "", new1: "", new2: "" });
const passwordSaving = ref(false);
const passwordMessage = ref("");
const passwordMessageType = ref("");

// Stats
const totalSessions = ref(0);
const totalMinutes = ref(0);
const today = new Date().toISOString().slice(0, 10);

async function saveProfile() {
  profileSaving.value = true;
  profileMessage.value = "";
  try {
    await updateProfile({ nickname: nickname.value });
    profileMessage.value = t("settings.profile.saved");
    profileMessageType.value = "success";
  } catch (err: any) {
    profileMessage.value = err.message || t("settings.profile.saveFailed");
    profileMessageType.value = "error";
  } finally {
    profileSaving.value = false;
  }
}

async function changePassword() {
  passwordMessage.value = "";
  if (!passwordForm.value.old || !passwordForm.value.new1 || !passwordForm.value.new2) {
    passwordMessage.value = t("settings.password.fillAll");
    passwordMessageType.value = "error";
    return;
  }
  if (passwordForm.value.new1 !== passwordForm.value.new2) {
    passwordMessage.value = t("settings.password.notMatch");
    passwordMessageType.value = "error";
    return;
  }
  if (passwordForm.value.new1.length < 6) {
    passwordMessage.value = t("settings.password.tooShort");
    passwordMessageType.value = "error";
    return;
  }

  passwordSaving.value = true;
  try {
    await apiChangePassword(passwordForm.value.old, passwordForm.value.new1);
    passwordMessage.value = t("settings.password.changed");
    passwordMessageType.value = "success";
    passwordForm.value = { old: "", new1: "", new2: "" };
  } catch (err: any) {
    passwordMessage.value = err.message || t("settings.password.changeFailed");
    passwordMessageType.value = "error";
  } finally {
    passwordSaving.value = false;
  }
}

onMounted(async () => {
  try {
    const data = await getPersonalReport();
    totalSessions.value = data.total_sessions || 0;
    totalMinutes.value = data.total_duration_minutes || 0;
  } catch {
    // defaults
  }
});
</script>

<style scoped>
.settings-page { display: grid; gap: 24px; }

.section-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.back-home-btn {
  padding: 8px 20px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
  color: var(--muted);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-home-btn:hover {
  border-color: var(--green, #25b87b);
  color: var(--green, #25b87b);
  background: rgba(37,184,123,0.05);
}
.settings-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; align-items: start; }
.settings-main { display: grid; gap: 20px; }
.settings-card { padding: 24px; border-radius: 14px; background: var(--paper); border: 1px solid var(--line); display: grid; gap: 14px; box-shadow: var(--shadow); }
.settings-card header { display: flex; align-items: center; gap: 12px; }
.settings-card h2 { color: var(--ink); font-size: 16px; margin: 0; }
.settings-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 10px; flex-shrink: 0; }
.tone-blue { background: rgba(91,140,255,0.1); color: #5b8cff; }
.tone-purple { background: rgba(139,92,246,0.1); color: #8b5cf6; }
.tone-orange { background: rgba(249,115,22,0.1); color: #f97316; }
.tone-green { background: rgba(37,184,123,0.1); color: #25b87b; }

.settings-card label { display: grid; gap: 6px; color: var(--muted); font-size: 13px; font-weight: 600; }
.settings-card input[type="text"], .settings-card input[type="password"], .settings-card select { padding: 10px 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); color: var(--ink); font-size: 14px; }
.readonly-input { opacity: 0.7; cursor: not-allowed; }
.outline-wide-button { min-height: 42px; border: 1px solid var(--line); border-radius: 9px; background: var(--panel); color: var(--muted); font-size: 14px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 24px; }
.outline-wide-button:hover { background: rgba(91,140,255,0.06); border-color: #5b8cff; }
.outline-wide-button:disabled { opacity: 0.5; cursor: not-allowed; }
.settings-message { font-size: 13px; padding: 8px 12px; border-radius: 6px; margin: 0; }
.settings-message.success { color: #25b87b; background: rgba(37,184,123,0.08); }
.settings-message.error { color: #ef4444; background: rgba(239,68,68,0.06); }

.settings-toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; }
.settings-toggle-row span { color: var(--muted); font-size: 13px; }
.settings-toggle-row input[type="checkbox"] { accent-color: #5b8cff; width: 18px; height: 18px; }
.settings-check { display: flex; align-items: center; gap: 10px; color: var(--muted); font-size: 13px; }
.settings-check input[type="checkbox"] { accent-color: #5b8cff; width: 16px; height: 16px; }
.storage-row { display: flex; justify-content: space-between; color: var(--muted); font-size: 13px; padding: 8px 0; }
.storage-row strong { color: var(--ink); }

/* side */
.settings-side { display: grid; gap: 16px; align-content: start; }
.settings-side-card { padding: 20px; border-radius: 14px; background: var(--paper); border: 1px solid var(--line); display: grid; gap: 12px; box-shadow: var(--shadow); }
.settings-side-card h2 { color: var(--ink); font-size: 15px; margin: 0; }
.side-icon { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 12px; }
.blue-solid { background: linear-gradient(135deg, #5b8cff, #60a5fa); color: #fff; }
.purple-solid { background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: #fff; }
.theme-solid { background: linear-gradient(135deg, #f59e0b, #fbbf24); color: #fff; }
.settings-side-card select { padding: 8px 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); color: var(--ink); font-size: 14px; }
.settings-side-card label { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
.settings-side-card input[type="checkbox"] { accent-color: #5b8cff; }
.system-info-list { display: grid; gap: 8px; }
.system-info-list div { display: flex; justify-content: space-between; }
.system-info-list dt { color: var(--muted); font-size: 12px; }
.system-info-list dd { color: var(--ink); font-size: 13px; margin: 0; }

@media (max-width: 1000px) { .settings-layout { grid-template-columns: 1fr; } }
</style>
