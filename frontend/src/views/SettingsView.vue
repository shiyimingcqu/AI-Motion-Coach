<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Settings</p>
        <h1>系统设置</h1>
        <p class="subtle">这些设置会保存在当前浏览器中，刷新页面后仍会保留。</p>
      </div>
      <span class="status-pill good">已自动保存</span>
    </header>

    <section class="settings-grid">
      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Training</p>
            <h2>训练偏好</h2>
          </div>
        </div>

        <label class="setting-row">
          <span>
            <strong>默认训练动作</strong>
            <small>进入训练时优先使用的动作类型</small>
          </span>
          <select v-model="settings.defaultExercise">
            <option value="squat">深蹲</option>
            <option value="push_up">俯卧撑</option>
            <option value="jumping_jack">开合跳</option>
          </select>
        </label>

        <label class="setting-row">
          <span>
            <strong>摄像头分辨率</strong>
            <small>实时检测时建议使用的采集清晰度</small>
          </span>
          <select v-model="settings.cameraResolution">
            <option value="720p">720p</option>
            <option value="1080p">1080p</option>
          </select>
        </label>
      </article>

      <article class="panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Experience</p>
            <h2>体验设置</h2>
          </div>
        </div>

        <label class="setting-row">
          <span>
            <strong>训练提示音</strong>
            <small>动作错误或完成计数时播放提示</small>
          </span>
          <input v-model="settings.soundEnabled" type="checkbox" />
        </label>

        <label class="setting-row">
          <span>
            <strong>保存训练视频</strong>
            <small>训练结束后保留本次分析视频</small>
          </span>
          <input v-model="settings.saveTrainingVideo" type="checkbox" />
        </label>

        <label class="setting-row">
          <span>
            <strong>深色训练面板</strong>
            <small>实时检测页使用更深的视觉风格</small>
          </span>
          <input v-model="settings.darkTrainingPanel" type="checkbox" />
        </label>
      </article>
    </section>

    <section class="panel">
      <div class="section-title">
        <div>
          <p class="eyebrow">Current Config</p>
          <h2>当前设置预览</h2>
        </div>
        <button class="secondary-button" type="button" @click="resetSettings">恢复默认</button>
      </div>
      <pre class="settings-preview">{{ settings }}</pre>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from "vue";

const STORAGE_KEY = "pose-evaluation-settings";

interface UserSettings {
  defaultExercise: string;
  cameraResolution: string;
  soundEnabled: boolean;
  saveTrainingVideo: boolean;
  darkTrainingPanel: boolean;
}

const defaultSettings: UserSettings = {
  defaultExercise: "squat",
  cameraResolution: "720p",
  soundEnabled: true,
  saveTrainingVideo: false,
  darkTrainingPanel: false
};

const settings = reactive<UserSettings>(loadSettings());

watch(
  settings,
  (value) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  },
  { deep: true }
);

function loadSettings(): UserSettings {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return { ...defaultSettings };
  }

  try {
    return { ...defaultSettings, ...JSON.parse(raw) };
  } catch {
    return { ...defaultSettings };
  }
}

function resetSettings() {
  Object.assign(settings, defaultSettings);
}
</script>
