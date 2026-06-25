<template>
  <div class="upload-page">
    <header class="section-page-header">
      <div>
        <h1>Video Upload Analysis / 视频上传分析</h1>
        <p>Upload and analyze training videos</p>
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
        <strong>{{ selectedFile ? selectedFile.name : "Drop your video here / 拖拽视频到此处" }}</strong>
        <span>or click to browse files (MP4, AVI, MOV up to 500MB)</span>

        <label class="upload-exercise-select">
          <span>Exercise / 动作</span>
          <select v-model="selectedExercise">
            <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
              {{ exerciseDisplayName(exercise.key) }}
            </option>
          </select>
        </label>

        <input
          ref="fileInput"
          class="hidden-input"
          type="file"
          accept="video/mp4,video/avi,video/quicktime,.mp4,.avi,.mov"
          @change="handleFileChange"
        />
        <button class="blue-action-button" type="button" @click="openFilePicker">
          Browse Files / 选择文件
        </button>
        <button
          v-if="selectedFile"
          class="blue-action-button upload-start-button"
          type="button"
          :disabled="uploadState === 'uploading'"
          @click="uploadVideo"
        >
          {{ uploadState === "uploading" ? "Analyzing... / 分析中..." : "Start Analysis / 开始分析" }}
        </button>

        <video v-if="localPreviewUrl" class="upload-preview-video" :src="localPreviewUrl" controls />
        <p v-if="message" class="upload-message" :class="{ danger: uploadState === 'failed' }">
          {{ message }}
        </p>
      </div>
    </section>

    <section class="analysis-history-card">
      <header>
        <h2>Analysis History / 分析历史</h2>
        <button class="link-button" type="button">View All</button>
      </header>

      <div class="analysis-list">
        <article v-for="item in analysisHistory" :key="item.id" class="analysis-row">
          <button class="play-button" type="button">
            <Play :size="27" />
          </button>
          <div class="analysis-file">
            <strong>
              <File :size="16" />
              {{ item.name }}
            </strong>
            <span>{{ item.date }} &nbsp;&nbsp; Duration: {{ item.duration }}</span>
          </div>

          <template v-if="item.status === 'completed'">
            <div class="analysis-stat">
              <span>Score</span>
              <strong class="stat-score">{{ item.score }}</strong>
            </div>
            <div class="analysis-stat">
              <span>Errors</span>
              <strong class="stat-error">{{ item.errors }}</strong>
            </div>
            <a
              v-if="item.reportUrl"
              class="report-button"
              :href="item.reportUrl"
              target="_blank"
              rel="noreferrer"
            >
              <BarChart3 :size="17" />
              View Report
            </a>
            <button v-else class="report-button" type="button">
              <BarChart3 :size="17" />
              View Report
            </button>
          </template>

          <span v-else class="processing-pill">
            <LoaderCircle :size="19" />
            Processing...
          </span>
        </article>
      </div>
    </section>

    <section class="upload-summary-grid">
      <article v-for="item in uploadStats" :key="item.label" class="upload-stat-card">
        <div>
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
        <span class="upload-stat-icon" :class="item.tone">
          <component :is="item.icon" :size="25" />
        </span>
      </article>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import {
  BarChart3,
  CheckCircle2,
  File,
  FileText,
  LoaderCircle,
  Play,
  Upload
} from "lucide-vue-next";

import { apiUpload } from "../api/client";
import { exercises } from "../stores/training";

interface AnalysisTask {
  task_id: string;
  exercise: string;
  source_uri: string;
  status: string;
  output_uri?: string | null;
}

interface UploadResponse {
  file_uri: string;
  task: AnalysisTask;
}

interface HistoryItem {
  id: string;
  name: string;
  date: string;
  duration: string;
  score?: number;
  errors?: number;
  status: "completed" | "processing";
  reportUrl?: string;
}

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const selectedExercise = ref("squat");
const isDragging = ref(false);
const uploadState = ref<"idle" | "ready" | "uploading" | "success" | "failed">("idle");
const message = ref("");
const latestTask = ref<AnalysisTask | null>(null);
const localPreviewUrl = ref("");

const defaultHistory: HistoryItem[] = [
  {
    id: "h1",
    name: "squat_session_001.mp4",
    date: "2026-06-25 14:30",
    duration: "2:45",
    score: 92,
    errors: 2,
    status: "completed"
  },
  {
    id: "h2",
    name: "pushup_training_023.mp4",
    date: "2026-06-25 13:15",
    duration: "1:30",
    score: 85,
    errors: 4,
    status: "completed"
  },
  {
    id: "h3",
    name: "plank_exercise_045.mp4",
    date: "2026-06-25 12:00",
    duration: "3:00",
    status: "processing"
  }
];

const analysisHistory = computed<HistoryItem[]>(() => {
  if (!latestTask.value) return defaultHistory;
  const uploadedName = selectedFile.value?.name ?? "uploaded_training_video.mp4";
  const reportUrl = latestTask.value.output_uri
    ? `/api/files/${encodeFilePath(latestTask.value.output_uri)}`
    : undefined;

  return [
    {
      id: latestTask.value.task_id,
      name: uploadedName,
      date: "Just now / 刚刚",
      duration: "new",
      score: uploadState.value === "success" ? 90 : undefined,
      errors: uploadState.value === "success" ? 3 : undefined,
      status: uploadState.value === "success" ? "completed" : "processing",
      reportUrl
    },
    ...defaultHistory
  ];
});

const uploadStats = computed(() => [
  { label: "Total Videos / 总视频数", value: 247 + (latestTask.value ? 1 : 0), icon: FileText, tone: "tone-blue" },
  { label: "Completed / 已完成", value: 245 + (uploadState.value === "success" ? 1 : 0), icon: CheckCircle2, tone: "tone-green" },
  { label: "Processing / 处理中", value: uploadState.value === "uploading" ? 3 : 2, icon: LoaderCircle, tone: "tone-orange" }
]);

function exerciseDisplayName(key: string) {
  const names: Record<string, string> = {
    squat: "Squat / 深蹲",
    pushup: "Push-up / 俯卧撑",
    jumping_jack: "Jumping Jack / 开合跳",
    plank: "Plank / 平板支撑"
  };
  return names[key] ?? key;
}

function encodeFilePath(path: string) {
  return path.replace(/\\/g, "/").split("/").map(encodeURIComponent).join("/");
}

function openFilePicker() {
  fileInput.value?.click();
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  chooseFile(input.files?.[0] ?? null);
}

function handleDrop(event: DragEvent) {
  isDragging.value = false;
  chooseFile(event.dataTransfer?.files?.[0] ?? null);
}

function chooseFile(file: File | null) {
  if (!file) return;

  if (!file.type.startsWith("video/") && !/\.(mp4|avi|mov)$/i.test(file.name)) {
    uploadState.value = "failed";
    message.value = "请选择 MP4、AVI 或 MOV 格式的视频文件。";
    return;
  }

  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value);
  }

  selectedFile.value = file;
  latestTask.value = null;
  localPreviewUrl.value = URL.createObjectURL(file);
  uploadState.value = "ready";
  message.value = `已选择：${file.name}`;
}

async function uploadVideo() {
  if (!selectedFile.value) {
    message.value = "请先选择一个训练视频。";
    return;
  }

  uploadState.value = "uploading";
  latestTask.value = {
    task_id: "processing-local",
    exercise: selectedExercise.value,
    source_uri: selectedFile.value.name,
    status: "processing"
  };
  message.value = "正在上传视频并生成分析报告，请稍候...";

  const formData = new FormData();
  formData.append("exercise", selectedExercise.value);
  formData.append("file", selectedFile.value);

  try {
    const result = await apiUpload<UploadResponse>("/videos/upload", formData);
    latestTask.value = result.task;
    uploadState.value = "success";
    message.value = `分析完成：${result.task.task_id}`;
  } catch {
    uploadState.value = "failed";
    latestTask.value = null;
    message.value = "上传失败，请确认后端服务已启动。";
  }
}
</script>
