<template>
  <div class="page settings-page">
    <button class="back-link" type="button" @click="goHome">
      <ArrowLeft :size="24" />
      返回首页
    </button>

    <header class="page-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h1>系统设置</h1>
        <p class="subtle">以下选项会保存在当前浏览器中。部分功能仍在开发中，可先配置并预览。</p>
      </div>
      <button class="secondary-button" type="button" @click="resetSettings">恢复默认</button>
    </header>

    <div class="settings-stack">
      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Experience</p>
            <h2>体验设置</h2>
          </div>
        </div>

        <label class="setting-row">
          <span>
            <strong>深色模式</strong>
            <small>开启后，全部界面切换为深色视觉风格</small>
          </span>
          <input v-model="settings.darkTrainingPanel" type="checkbox" />
        </label>

        <label class="setting-row">
          <span>
            <strong>界面语言</strong>
            <small>切换中英文界面（完整翻译开发中）</small>
          </span>
          <select v-model="settings.language">
            <option v-for="option in languageOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>
      </section>

      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Notifications</p>
            <h2>通知设置</h2>
          </div>
        </div>

        <label class="setting-row">
          <span>
            <strong>消息通知</strong>
            <small>控制顶栏通知红点和消息弹层是否显示</small>
          </span>
          <input v-model="settings.notificationsEnabled" type="checkbox" />
        </label>

        <label class="setting-row">
          <span>
            <strong>训练完成提醒</strong>
            <small>视频分析任务完成后发送浏览器通知（开发中）</small>
          </span>
          <input v-model="settings.trainingCompleteReminder" type="checkbox" />
        </label>
      </section>

      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Camera</p>
            <h2>摄像头设置</h2>
          </div>
        </div>

        <label class="setting-row">
          <span>
            <strong>摄像头分辨率</strong>
            <small>影响实时检测页的画质与性能（开发中）</small>
          </span>
          <select v-model="settings.cameraResolution">
            <option
              v-for="option in cameraResolutionOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="setting-row">
          <span>
            <strong>摄像头镜像</strong>
            <small>自拍视角左右翻转，更符合训练习惯（开发中）</small>
          </span>
          <input v-model="settings.cameraMirror" type="checkbox" />
        </label>
      </section>

      <section class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Data</p>
            <h2>数据管理</h2>
          </div>
        </div>

        <p class="settings-note">导出当前系统设置 JSON，便于备份或在其他设备恢复（导入功能开发中）。</p>

        <div class="settings-data-actions">
          <button class="secondary-button" type="button" @click="handleExport">
            <Download :size="18" />
            导出设置
          </button>
          <button class="secondary-button" type="button" @click="triggerImport">
            <Upload :size="18" />
            导入设置
          </button>
          <input
            ref="importInputRef"
            class="hidden-input"
            type="file"
            accept="application/json,.json"
            @change="handleImportFile"
          />
        </div>

        <pre class="settings-preview">{{ settingsPreview }}</pre>
        <p v-if="dataMessage" class="settings-status-message">{{ dataMessage }}</p>
      </section>

      <section class="panel settings-danger-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Danger Zone</p>
            <h2>危险操作</h2>
          </div>
        </div>

        <p class="settings-note danger">
          清除后将删除本浏览器中的系统设置、个人资料、头像与登录状态，此操作不可撤销（功能开发中）。
        </p>

        <button class="danger-button" type="button" @click="handleClearCache">
          <Trash2 :size="18" />
          清除本地缓存
        </button>
        <p v-if="dangerMessage" class="settings-status-message">{{ dangerMessage }}</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { storeToRefs } from "pinia";
import { ArrowLeft, Download, Trash2, Upload } from "lucide-vue-next";
import { useRouter } from "vue-router";

import {
  CAMERA_RESOLUTION_OPTIONS,
  LANGUAGE_OPTIONS,
  useSettingsStore
} from "../stores/settings";

const router = useRouter();
const settingsStore = useSettingsStore();
const { settings } = storeToRefs(settingsStore);

const languageOptions = LANGUAGE_OPTIONS;
const cameraResolutionOptions = CAMERA_RESOLUTION_OPTIONS;

const importInputRef = ref<HTMLInputElement | null>(null);
const dataMessage = ref("");
const dangerMessage = ref("");

const settingsPreview = computed(() => settingsStore.exportSettingsJson());

function goHome() {
  router.push("/");
}

function resetSettings() {
  settingsStore.resetSettings();
  dataMessage.value = "已恢复默认设置。";
  dangerMessage.value = "";
}

function handleExport() {
  const blob = new Blob([settingsStore.exportSettingsJson()], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "pose-evaluation-settings.json";
  link.click();
  URL.revokeObjectURL(url);
  dataMessage.value = "设置已导出为 JSON 文件。";
}

function triggerImport() {
  importInputRef.value?.click();
}

function handleImportFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";

  if (!file) {
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    const result = settingsStore.importSettingsJson(String(reader.result ?? ""));
    dataMessage.value = result.message;
  };
  reader.readAsText(file);
}

function handleClearCache() {
  if (!window.confirm("确定要清除本地缓存吗？此操作开发中，当前不会真正删除数据。")) {
    return;
  }

  const result = settingsStore.clearLocalCache();
  dangerMessage.value = result.message;
}
</script>
