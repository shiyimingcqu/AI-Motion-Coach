<template>
  <div class="upload-page">
    <header class="section-page-header">
      <div>
        <h1>{{ $t("videoUpload.title") }}</h1>
        <p>{{ $t("videoUpload.uploadVideo") }}</p>
      </div>
    </header>

    <section class="upload-main-card">
      <h2>{{ $t("videoUpload.uploadVideo") }}</h2>
      <div
        class="upload-drop-card"
        :class="{ active: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <Upload :size="48" />
        <strong>{{ selectedFile ? selectedFile.name : $t("videoUpload.dropHere") }}</strong>
        <span>or click to browse files (MP4, AVI, MOV up to 500MB)</span>

        <label class="upload-exercise-select">
          <span>{{ $t("videoUpload.exerciseLabel") }}</span>
          <select v-model="selectedExercise">
            <option v-for="exercise in exercises" :key="exercise.key" :value="exercise.key">
              {{ exerciseDisplayName(exercise.key) }}
            </option>
          </select>
        </label>

        <label class="upload-exercise-select">
          <span>{{ $t("videoUpload.cameraView") }}</span>
          <select v-model="selectedCameraView">
            <option value="front">{{ $t("videoUpload.front") }}</option>
            <option value="side">{{ $t("videoUpload.side") }}</option>
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
          {{ $t("videoUpload.browseFiles") }}
        </button>
        <div class="upload-info-before-send" v-if="selectedFile">
          {{ $t("videoUpload.willUpload", { exercise: exerciseDisplayName(selectedExercise), view: selectedCameraView === 'side' ? $t('videoUpload.side') : $t('videoUpload.front') }) }}
        </div>
        <button
          v-if="selectedFile"
          class="blue-action-button upload-start-button"
          type="button"
          :disabled="uploadState === 'uploading'"
          @click="uploadVideo"
        >
          {{ uploadState === "uploading" ? $t("videoUpload.uploading") : $t("videoUpload.startAnalysis") }}
        </button>

        <video v-if="localPreviewUrl" class="upload-preview-video" :src="localPreviewUrl" controls />
        <p v-if="message" class="upload-message" :class="{ danger: uploadState === 'failed' }">
          {{ message }}
        </p>
      </div>
    </section>

    <section class="analysis-history-card">
      <header>
        <h2>{{ $t("videoUpload.analysisHistory") }}</h2>
        <button class="link-button" type="button">View All</button>
      </header>

      <div class="analysis-list">
        <article v-for="item in analysisHistory" :key="item.id" class="analysis-row" :class="{ 'analysis-row--completed': item.status === 'completed' }">
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
            <span class="completed-badge">
              <CheckCircle2 :size="14" />
              {{ $t("videoUpload.completed") }}
            </span>
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

          <span v-else-if="item.status === 'failed'" class="failed-pill">
            <XCircle :size="19" />
            {{ $t("videoUpload.failed") }}
          </span>

          <span v-else class="processing-pill">
            <LoaderCircle :size="19" />
            {{ $t("videoUpload.processing") }}
          </span>

          <button
            class="delete-button"
            type="button"
            :title="$t('videoUpload.deleteRecord')"
            @click.stop="handleDeleteTask(item.id)"
          >
            <Trash2 :size="16" />
          </button>
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
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import {
  BarChart3,
  CheckCircle2,
  File,
  FileText,
  LoaderCircle,
  Play,
  Trash2,
  Upload,
  XCircle
} from "lucide-vue-next";

import { apiDelete, apiGet, apiUpload } from "../api/client";
import { useAuthStore } from "../stores/auth";
import { exercises } from "../stores/training";

interface AnalysisTask {
  task_id: string;
  exercise: string;
  source_uri: string;
  status: string;
  output_uri?: string | null;
  created_at?: string;
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
  status: "completed" | "processing" | "failed";
  reportUrl?: string;
}

const { t } = useI18n();

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const selectedExercise = ref("squat");
const selectedCameraView = ref("front");
const isDragging = ref(false);
const uploadState = ref<"idle" | "ready" | "uploading" | "success" | "failed">("idle");
const message = ref("");
const latestTask = ref<AnalysisTask | null>(null);
const localPreviewUrl = ref("");
const allTasks = ref<AnalysisTask[]>([]);
const tasksLoading = ref(true);

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.role === "admin");

function formatTime(iso?: string): string {
  if (!iso) return "-";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

const analysisHistory = computed<HistoryItem[]>(() => {
  const items: HistoryItem[] = (allTasks.value || []).map(t => ({
    id: t.task_id,
    name: t.source_uri?.split("/").pop() || t.task_id.slice(0, 12) + ".mp4",
    date: formatTime(t.created_at),
    duration: "-",
    status: t.status === "success" || t.status === "completed" ? "completed" : t.status === "failed" ? "failed" : "processing",
    reportUrl: t.output_uri ? `/api/files/${t.output_uri.replace(/\\/g, "/").split("/").map(encodeURIComponent).join("/")}` : undefined,
  }));

  // Add latest upload at top if not yet in backend list
  if (latestTask.value && !items.some(i => i.id === latestTask.value?.task_id)) {
    const uploadedName = selectedFile.value?.name ?? "uploaded_training_video.mp4";
    items.unshift({
      id: latestTask.value.task_id,
      name: uploadedName,
      date: t("videoUpload.justNow"),
      duration: "new",
      score: uploadState.value === "success" ? 90 : undefined,
      errors: uploadState.value === "success" ? 3 : undefined,
      status: uploadState.value === "success" ? "completed" : "processing",
      reportUrl: latestTask.value.output_uri ? `/api/files/${encodeFilePath(latestTask.value.output_uri)}` : undefined,
    });
  }

  return items.slice(0, 20);
});

const uploadStats = computed(() => {
  const total = allTasks.value.length + (latestTask.value ? 1 : 0);
  const completed = allTasks.value.filter(t => t.status === "success" || t.status === "completed").length + (uploadState.value === "success" ? 1 : 0);
  const processing = allTasks.value.filter(t => t.status === "pending" || t.status === "processing").length + (uploadState.value === "uploading" ? 1 : 0);
  return [
    { label: t("videoUpload.summary_total"), value: total || "--", icon: FileText, tone: "tone-blue" },
    { label: t("videoUpload.summary_completed"), value: completed || "--", icon: CheckCircle2, tone: "tone-green" },
    { label: t("videoUpload.summary_processing"), value: processing || "--", icon: LoaderCircle, tone: "tone-orange" },
  ];
});

function exerciseDisplayName(key: string) {
  const names: Record<string, string> = {
    squat: t("exercises.squat"),
    push_up: t("exercises.push_up"),
    jumping_jack: t("exercises.jumping_jack"),
    plank: t("exercises.plank")
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
    message.value = t("videoUpload.selectFile");
    return;
  }

  if (localPreviewUrl.value) {
    URL.revokeObjectURL(localPreviewUrl.value);
  }

  selectedFile.value = file;
  latestTask.value = null;
  localPreviewUrl.value = URL.createObjectURL(file);
  uploadState.value = "ready";
  message.value = t("videoUpload.fileSelected", { name: file.name });
}

async function uploadVideo() {
  if (!selectedFile.value) {
    message.value = t("videoUpload.noFile");
    return;
  }

  uploadState.value = "uploading";
  latestTask.value = {
    task_id: "processing-local",
    exercise: selectedExercise.value,
    source_uri: selectedFile.value.name,
    status: "processing"
  };
  message.value = t("videoUpload.uploadingMsg");

  const formData = new FormData();
  formData.append("exercise", selectedExercise.value);
  formData.append("camera_view", selectedCameraView.value);
  formData.append("file", selectedFile.value);
  console.log("[Upload] camera_view:", selectedCameraView.value, "exercise:", selectedExercise.value);

  try {
    const result = await apiUpload<UploadResponse>("/videos/upload", formData);
    latestTask.value = result.task;
    uploadState.value = "success";
    message.value = `${t("videoUpload.completeMsg")}${result.task.task_id}`;
    // Refresh task list
    await loadTasks();
  } catch {
    uploadState.value = "failed";
    latestTask.value = null;
    message.value = t("videoUpload.uploadFailed");
  }
}

async function loadTasks() {
  tasksLoading.value = true;
  try {
    const data = await apiGet<{ items: any[] }>("/analysis/tasks");
    allTasks.value = data.items || [];
  } catch {
    allTasks.value = [];
  } finally {
    tasksLoading.value = false;
  }
}

async function handleDeleteTask(task_id: string) {
  if (!confirm(t("videoUpload.deleteConfirm"))) return;
  try {
    await apiDelete(`/analysis/tasks/${task_id}`);
    allTasks.value = allTasks.value.filter(t => t.task_id !== task_id);
  } catch (err: any) {
    alert(t("videoUpload.deleteFailed", { error: err.message || t("videoUpload.networkError") }));
  }
}

onMounted(loadTasks);
</script>
