<template>
  <div class="settings-page">
    <header class="section-page-header">
      <div>
        <h1>Settings / 系统设置</h1>
        <p>Configure system preferences and manage your account</p>
      </div>
    </header>

    <section class="settings-layout">
      <div class="settings-main">
        <article class="settings-card">
          <header>
            <span class="settings-icon tone-blue"><User :size="22" /></span>
            <h2>Profile / 个人资料</h2>
          </header>
          <StateDisplay v-if="profileLoading" type="loading" skeleton="text" />
          <template v-else>
            <label>
              Username / 用户名
              <input :value="authStore.username" type="text" readonly class="readonly-input" />
            </label>
            <label>
              Role / 角色
              <input :value="authStore.isAdmin ? 'Admin / 管理员' : 'User / 用户'" type="text" readonly class="readonly-input" />
            </label>
            <label>
              Nickname / 昵称
              <input v-model="nickname" type="text" placeholder="设置昵称" />
            </label>
            <button
              class="outline-wide-button"
              type="button"
              :disabled="profileSaving"
              @click="saveProfile"
            >
              {{ profileSaving ? 'Saving... / 保存中...' : 'Save Profile / 保存资料' }}
            </button>
            <p v-if="profileMessage" class="settings-message" :class="profileMessageType">{{ profileMessage }}</p>
          </template>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-purple"><Lock :size="22" /></span>
            <h2>Change Password / 修改密码</h2>
          </header>
          <label>
            Current Password / 当前密码
            <input v-model="passwordForm.old" type="password" placeholder="输入当前密码" />
          </label>
          <label>
            New Password / 新密码
            <input v-model="passwordForm.new1" type="password" placeholder="输入新密码（至少6位）" />
          </label>
          <label>
            Confirm Password / 确认密码
            <input v-model="passwordForm.new2" type="password" placeholder="再次输入新密码" />
          </label>
          <button
            class="outline-wide-button"
            type="button"
            :disabled="passwordSaving"
            @click="changePassword"
          >
            {{ passwordSaving ? 'Saving... / 保存中...' : 'Change Password / 修改密码' }}
          </button>
          <p v-if="passwordMessage" class="settings-message" :class="passwordMessageType">{{ passwordMessage }}</p>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-orange"><Bell :size="22" /></span>
            <h2>Notifications / 通知设置</h2>
          </header>
          <label v-for="item in notifications" :key="item" class="settings-toggle-row">
            <span>{{ item }}</span>
            <input type="checkbox" :checked="item !== 'Weekly reports / 周报'" />
          </label>
        </article>

        <article class="settings-card">
          <header>
            <span class="settings-icon tone-green"><Database :size="22" /></span>
            <h2>Data & Storage / 数据与存储</h2>
          </header>
          <div class="storage-row">
            <span>Storage Used / 已使用存储</span>
            <strong>{{ totalSessions }} sessions / {{ totalMinutes }} min</strong>
          </div>
          <label class="settings-check">
            <input type="checkbox" checked />
            Auto-backup / 自动备份
          </label>
        </article>
      </div>

      <aside class="settings-side">
        <article class="settings-side-card blue-side-card">
          <span class="side-icon blue-solid"><Globe2 :size="26" /></span>
          <h2>Language / 语言</h2>
          <select>
            <option>English / 英语</option>
            <option>Chinese / 中文</option>
          </select>
        </article>

        <article class="settings-side-card purple-side-card">
          <span class="side-icon purple-solid"><Shield :size="26" /></span>
          <h2>Privacy / 隐私</h2>
          <label><input type="checkbox" checked /> Data analytics / 数据分析</label>
          <label><input type="checkbox" /> Share progress / 分享进度</label>
        </article>

        <article class="settings-side-card">
          <h2>System Info / 系统信息</h2>
          <dl class="system-info-list">
            <div><dt>Version</dt><dd>v2.1.0</dd></div>
            <div><dt>Last Updated</dt><dd>{{ today }}</dd></div>
            <div><dt>AI Model</dt><dd>PoseNet v4</dd></div>
          </dl>
        </article>
      </aside>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Bell, Database, Globe2, Lock, Shield, User } from "lucide-vue-next";
import StateDisplay from "@/components/StateDisplay.vue";
import { useAuthStore } from "@/stores/auth";
import { getPersonalReport } from "@/api/reports";
import { updateProfile, changePassword as apiChangePassword } from "@/api/users";

const authStore = useAuthStore();

const notifications = [
  "Training reminders / 训练提醒",
  "Achievement alerts / 成就提醒",
  "Error notifications / 错误通知",
  "Weekly reports / 周报",
];

const nickname = ref(authStore.username);
const profileLoading = ref(false);
const profileSaving = ref(false);
const profileMessage = ref("");
const profileMessageType = ref("");

const passwordForm = ref({ old: "", new1: "", new2: "" });
const passwordSaving = ref(false);
const passwordMessage = ref("");
const passwordMessageType = ref("");

const totalSessions = ref(0);
const totalMinutes = ref(0);
const today = new Date().toISOString().slice(0, 10);

async function saveProfile() {
  profileSaving.value = true;
  profileMessage.value = "";
  try {
    await updateProfile({ nickname: nickname.value });
    profileMessage.value = "Profile saved / 资料已保存";
    profileMessageType.value = "success";
  } catch (err: unknown) {
    profileMessage.value = err instanceof Error ? err.message : "保存失败";
    profileMessageType.value = "error";
  } finally {
    profileSaving.value = false;
  }
}

async function changePassword() {
  passwordMessage.value = "";
  if (!passwordForm.value.old || !passwordForm.value.new1 || !passwordForm.value.new2) {
    passwordMessage.value = "请填写所有密码字段";
    passwordMessageType.value = "error";
    return;
  }
  if (passwordForm.value.new1 !== passwordForm.value.new2) {
    passwordMessage.value = "两次输入的新密码不一致";
    passwordMessageType.value = "error";
    return;
  }
  if (passwordForm.value.new1.length < 6) {
    passwordMessage.value = "新密码至少6位";
    passwordMessageType.value = "error";
    return;
  }

  passwordSaving.value = true;
  try {
    await apiChangePassword(passwordForm.value.old, passwordForm.value.new1);
    passwordMessage.value = "Password changed / 密码已修改";
    passwordMessageType.value = "success";
    passwordForm.value = { old: "", new1: "", new2: "" };
  } catch (err: unknown) {
    passwordMessage.value = err instanceof Error ? err.message : "修改失败";
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
    // use defaults
  }
});
</script>

<style scoped>
.settings-page { display: grid; gap: 24px; }
.settings-layout { display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; align-items: start; }
.settings-main { display: grid; gap: 20px; }
.settings-card { padding: 24px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 14px; }
.settings-card header { display: flex; align-items: center; gap: 12px; }
.settings-card h2 { color: #f8fafc; font-size: 16px; margin: 0; }
.settings-icon { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 10px; flex-shrink: 0; }
.tone-blue { background: rgba(59,130,246,0.1); color: #60a5fa; }
.tone-purple { background: rgba(139,92,246,0.1); color: #a78bfa; }
.tone-orange { background: rgba(245,158,11,0.1); color: #fbbf24; }
.tone-green { background: rgba(16,185,129,0.1); color: #34d399; }

.settings-card label { display: grid; gap: 6px; color: #94a3b8; font-size: 13px; font-weight: 600; }
.settings-card input[type="text"], .settings-card input[type="password"], .settings-card select { padding: 10px 14px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; font-size: 14px; }
.readonly-input { opacity: 0.7; cursor: not-allowed; }
.outline-wide-button { min-height: 42px; border: 1px solid rgba(59,130,246,0.1); border-radius: 9px; background: rgba(8,13,26,0.5); color: #cbd5e1; font-size: 14px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; padding: 0 24px; }
.outline-wide-button:hover { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.2); }
.outline-wide-button:disabled { opacity: 0.5; cursor: not-allowed; }
.settings-message { font-size: 13px; padding: 8px 12px; border-radius: 6px; margin: 0; }
.settings-message.success { color: #34d399; background: rgba(16,185,129,0.08); }
.settings-message.error { color: #f87171; background: rgba(239,68,68,0.08); }

.settings-toggle-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; }
.settings-toggle-row span { color: #94a3b8; font-size: 13px; }
.settings-toggle-row input[type="checkbox"] { accent-color: #3b82f6; width: 18px; height: 18px; }
.settings-check { display: flex; align-items: center; gap: 10px; color: #94a3b8; font-size: 13px; }
.settings-check input[type="checkbox"] { accent-color: #3b82f6; width: 16px; height: 16px; }
.storage-row { display: flex; justify-content: space-between; color: #94a3b8; font-size: 13px; padding: 8px 0; }
.storage-row strong { color: #f8fafc; }

.settings-side { display: grid; gap: 16px; align-content: start; }
.settings-side-card { padding: 20px; border-radius: 14px; background: linear-gradient(180deg, rgba(15,23,42,0.96), rgba(8,13,26,0.98)); border: 1px solid rgba(59,130,246,0.1); display: grid; gap: 12px; }
.settings-side-card h2 { color: #f8fafc; font-size: 15px; margin: 0; }
.side-icon { width: 44px; height: 44px; display: grid; place-items: center; border-radius: 12px; }
.blue-solid { background: linear-gradient(135deg, #3b82f6, #60a5fa); color: #fff; }
.purple-solid { background: linear-gradient(135deg, #8b5cf6, #a78bfa); color: #fff; }
.settings-side-card select { padding: 8px 12px; border: 1px solid rgba(59,130,246,0.1); border-radius: 8px; background: rgba(8,13,26,0.7); color: #f8fafc; font-size: 14px; }
.settings-side-card label { display: flex; align-items: center; gap: 8px; color: #94a3b8; font-size: 13px; }
.settings-side-card input[type="checkbox"] { accent-color: #3b82f6; }
.system-info-list { display: grid; gap: 8px; }
.system-info-list div { display: flex; justify-content: space-between; }
.system-info-list dt { color: #64748b; font-size: 12px; }
.system-info-list dd { color: #f8fafc; font-size: 13px; margin: 0; }

@media (max-width: 1000px) { .settings-layout { grid-template-columns: 1fr; } }
</style>
