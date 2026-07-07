<template>
  <div class="page upload-page">
    <div v-if="finishPending" class="finish-overlay" role="dialog" aria-modal="true" aria-label="分析中">
      <div class="finish-modal">
        <div class="finish-spinner" aria-hidden="true"></div>
        <strong>正在完成分析</strong>
        <p>{{ finishStatusText }}</p>
      </div>
    </div>

    <!-- 上传前：独立上传模板 -->
    <template v-if="!showAnalysisWorkspace">
      <header class="section-page-header">
        <div>
          <h1>Video Upload Analysis / 视频上传分析</h1>
          <p>上传训练视频，使用与实时检测相同的姿态识别与分析引擎</p>
        </div>
      </header>

      <section class="upload-main-card">
        <h2>Upload Video / 上传视频</h2>
        <div
          class="upload-drop-card"
          :class="{ active: isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <Upload :size="48" />
          <strong>Drop your video here / 拖拽视频到此处</strong>
          <span>支持 MP4、WebM、MOV、AVI（最大 500MB）</span>

          <label class="upload-exercise-select">
            <span>Exercise / 动作</span>
            <select v-model="selectedExercise">
              <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
                {{ exercise.name }}
              </option>
            </select>
          </label>

          <input
            ref="fileInput"
            class="hidden-input"
            type="file"
            accept="video/mp4,video/webm,video/avi,video/quicktime,.mp4,.webm,.avi,.mov"
            @change="handleFileChange"
          />
          <button class="blue-action-button" type="button" @click="openFilePicker">
            Browse Files / 选择文件
          </button>

          <p v-if="message" class="upload-message" :class="{ danger: !!cameraError }">
            {{ cameraError || message }}
          </p>
        </div>
      </section>
    </template>

    <!-- 上传后：与实时检测视频分析相同的双栏版面 -->
    <template v-else>
      <header class="page-header">
        <div>
          <p class="eyebrow">Video Analysis</p>
          <h1>{{ exerciseMeta.name }} 视频分析</h1>
          <p class="subtle">{{ selectedFile?.name }}</p>
        </div>
        <div class="header-actions">
          <select v-model="selectedExercise" class="exercise-select" :disabled="analyzing">
            <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
              {{ exercise.name }}
            </option>
          </select>
          <span class="status-pill" :class="connectionClass">{{ statusLabel }}</span>
          <button class="secondary-button" type="button" :disabled="analyzing" @click="openFilePicker">
            <UploadCloud :size="18" />
            更换视频
          </button>
          <button
            class="primary-button"
            type="button"
            :disabled="analyzing"
            @click="startAnalysis"
          >
            <Play :size="18" />
            {{ analyzing ? "分析中..." : "开始分析" }}
          </button>
          <input
            ref="fileInput"
            class="hidden-input"
            type="file"
            accept="video/mp4,video/webm,video/avi,video/quicktime,.mp4,.webm,.avi,.mov"
            @change="handleFileChange"
          />
        </div>
      </header>

      <section class="training-cockpit">
        <div class="camera-panel">
          <video
            ref="videoRef"
            autoplay
            muted
            playsinline
            class="camera-video upload-analysis-video"
          ></video>
          <canvas ref="overlayRef" class="pose-overlay" aria-label="姿态骨架"></canvas>
          <div v-if="poseStatus" class="pose-status">{{ poseStatus }}</div>
        </div>

        <aside class="metric-rail">
          <div>
            <p class="eyebrow">Live Metrics</p>
            <h2>实时数据面板</h2>
          </div>
          <MetricTile label="当前动作" :value="exerciseMeta.name" :hint="selectedExercise" />
          <MetricTile label="阶段" :value="displayStage" hint="当前动作阶段" />
          <MetricTile label="评分" :value="displayScore" hint="分析评分" />

          <div v-if="message" class="alert-line">{{ message }}</div>
          <div v-if="cameraError" class="alert-line danger">{{ cameraError }}</div>

          <div class="error-stack error-stack--errors">
            <strong>错误提示</strong>
            <span v-if="trainingState === 'idle'" class="stack-empty">--</span>
            <template v-else>
              <span v-if="store.errors.length === 0" class="stack-empty">暂无错误</span>
              <span v-for="error in store.errors" :key="error">{{ error }}</span>
            </template>
          </div>

          <div class="error-stack error-stack--advice">
            <strong>动作建议</strong>
            <span v-if="trainingState === 'idle'" class="stack-empty">--</span>
            <template v-else>
              <span v-if="store.feedbacks.length === 0" class="stack-empty">暂无建议</span>
              <span v-for="advice in store.feedbacks" :key="advice">{{ advice }}</span>
            </template>
          </div>

          <p class="upload-analysis-hint">
            分析结束后将自动跳转到反馈页，可查看完整错误分析与 AI 建议。
          </p>
        </aside>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { Play, Upload, UploadCloud } from "lucide-vue-next";

import MetricTile from "../components/MetricTile.vue";
import { useRealtimeVideoTest } from "../composables/useRealtimeVideoTest";
import { exercises, useTrainingStore } from "../stores/training";

const store = useTrainingStore();
const fileInput = ref<HTMLInputElement | null>(null);
const videoRef = ref<HTMLVideoElement | null>(null);
const overlayRef = ref<HTMLCanvasElement | null>(null);
const selectedFile = ref<File | null>(null);
const selectedExercise = ref("squat");
const isDragging = ref(false);
const showAnalysisWorkspace = ref(false);

let previewUrl = "";

const {
  trainingState,
  poseStatus,
  cameraError,
  message,
  analyzing,
  finishPending,
  finishStatusText,
  analyzeVideoFile,
  cleanup,
} = useRealtimeVideoTest({
  exercise: selectedExercise,
  videoRef,
  overlayRef,
});

const exerciseMeta = computed(
  () => exercises.find((item) => item.key === selectedExercise.value) ?? exercises[0],
);

const statusLabel = computed(() => {
  const labels: Record<string, string> = {
    idle: "等待分析",
    connecting: "正在连接",
    running: "分析中",
    paused: "已暂停",
    finished: "已完成",
    error: "连接异常",
  };
  return labels[trainingState.value] ?? trainingState.value;
});

const connectionClass = computed(() => {
  if (trainingState.value === "running" || trainingState.value === "finished") return "good";
  if (trainingState.value === "error") return "danger";
  return "idle";
});

const displayStage = computed(() => {
  if (trainingState.value === "idle") return "--";
  return store.stage;
});

const displayScore = computed(() => {
  if (trainingState.value === "idle") return "--";
  return store.score;
});

watch(selectedExercise, (exercise) => {
  store.setExercise(exercise);
});

function revokePreviewUrl() {
  if (previewUrl) {
    URL.revokeObjectURL(previewUrl);
    previewUrl = "";
  }
}

function previewSelectedFile(file: File) {
  revokePreviewUrl();
  previewUrl = URL.createObjectURL(file);

  if (videoRef.value) {
    const stream = videoRef.value.srcObject as MediaStream | null;
    stream?.getTracks().forEach((track) => track.stop());
    videoRef.value.srcObject = null;
    videoRef.value.src = previewUrl;
    videoRef.value.loop = false;
    videoRef.value.currentTime = 0;
    void videoRef.value.play().catch(() => undefined);
  }
}

function openFilePicker() {
  fileInput.value?.click();
}

async function chooseFile(file: File | null) {
  if (!file) return;

  if (!file.type.startsWith("video/") && !/\.(mp4|webm|avi|mov)$/i.test(file.name)) {
    message.value = "请选择 MP4、WebM、AVI 或 MOV 格式的视频文件。";
    return;
  }

  cameraError.value = "";
  selectedFile.value = file;
  store.setExercise(selectedExercise.value);
  showAnalysisWorkspace.value = true;
  message.value = `已选择：${file.name}`;

  await nextTick();
  previewSelectedFile(file);
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  void chooseFile(input.files?.[0] ?? null);
  input.value = "";
}

function handleDrop(event: DragEvent) {
  isDragging.value = false;
  void chooseFile(event.dataTransfer?.files?.[0] ?? null);
}

async function startAnalysis() {
  if (!selectedFile.value) {
    message.value = "请先选择一个训练视频。";
    return;
  }
  await analyzeVideoFile(selectedFile.value);
}

onBeforeUnmount(() => {
  revokePreviewUrl();
  cleanup();
});
</script>

<style scoped>
.hidden-input {
  display: none;
}

.exercise-select {
  min-height: 42px;
  padding: 0 12px;
  border: 1px solid var(--line, #d5ded2);
  border-radius: 6px;
  background: var(--panel, #111827);
  color: var(--ink, #e6edf7);
  font-size: 14px;
}

.upload-analysis-video {
  object-fit: contain;
}

.upload-analysis-hint {
  margin: 0;
  color: var(--muted, #69756e);
  font-size: 12px;
  line-height: 1.6;
}

.upload-message.danger {
  color: #ef3f08 !important;
}

.finish-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.52);
  backdrop-filter: blur(4px);
}

.finish-modal {
  width: min(100%, 360px);
  display: grid;
  gap: 12px;
  justify-items: center;
  padding: 28px 24px;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 22px 60px rgba(15, 23, 42, 0.22);
  text-align: center;
}

.finish-modal strong {
  color: #16211b;
  font-size: 18px;
}

.finish-modal p {
  margin: 0;
  color: #5f6b63;
  font-size: 14px;
  line-height: 1.5;
}

.finish-spinner {
  width: 44px;
  height: 44px;
  border: 4px solid rgba(59, 130, 246, 0.16);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: finish-spin 0.8s linear infinite;
}

@keyframes finish-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
