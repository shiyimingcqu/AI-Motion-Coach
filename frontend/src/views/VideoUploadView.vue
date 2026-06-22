<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Async Analysis</p>
        <h1>视频上传分析</h1>
        <p class="subtle">上传后进入分析队列，任务完成后在右侧展示带骨架标注的输出视频。</p>
      </div>
    </header>

    <section class="video-workspace">
      <section
        class="upload-zone"
        :class="{ active: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
      >
        <UploadCloud :size="44" />
        <strong>{{ selectedFile ? selectedFile.name : "拖入训练视频或点击选择" }}</strong>
        <span>{{ helperText }}</span>

        <label class="select-row">
          <span>选择动作</span>
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
          accept="video/mp4,video/avi,video/quicktime,.mp4,.avi,.mov"
          @change="handleFileChange"
        />

        <div v-if="localPreviewUrl" class="video-preview">
          <div class="video-label">源视频预览</div>
          <video :src="localPreviewUrl" controls></video>
        </div>

        <div class="upload-actions">
          <button class="secondary-button" type="button" @click="openFilePicker">
            <FolderOpen :size="18" />
            选择视频
          </button>
          <button
            class="primary-button"
            type="button"
            :disabled="!selectedFile || uploadState === 'uploading'"
            @click="uploadVideo"
          >
            <Rocket :size="18" />
            {{ uploadState === "uploading" ? "分析中..." : "开始分析" }}
          </button>
        </div>

        <div v-if="message" class="alert-line" :class="{ danger: uploadState === 'failed' }">
          {{ message }}
        </div>
      </section>

      <section class="result-panel">
        <div class="section-title">
          <div>
            <p class="eyebrow">Output Preview</p>
            <h2>输出视频展示窗口</h2>
          </div>
          <span class="status-pill" :class="statusClass">{{ taskLabel }}</span>
        </div>

        <div v-if="outputVideoUrl" class="output-video-card">
          <video :key="outputVideoUrl" :src="outputVideoUrl" controls preload="metadata"></video>
          <div class="output-actions">
            <a class="secondary-button" :href="outputVideoUrl" target="_blank" rel="noreferrer">
              <ExternalLink :size="18" />
              新窗口打开
            </a>
            <a class="primary-button" :href="outputVideoUrl" download>
              <Download :size="18" />
              下载结果
            </a>
          </div>
        </div>
        <div v-else class="empty-result">
          <Film :size="38" />
          <strong>{{ uploadState === "uploading" ? "正在生成输出视频" : "等待输出视频" }}</strong>
          <span>分析完成后，这里会自动显示带骨架标注和帧信息的结果视频。</span>
        </div>

        <div class="progress-block">
          <div class="progress-line">
            <span :style="{ width: `${progress}%` }"></span>
          </div>
          <strong>{{ progress }}%</strong>
        </div>

        <dl v-if="latestTask" class="task-meta">
          <div>
            <dt>任务 ID</dt>
            <dd>{{ latestTask.task_id }}</dd>
          </div>
          <div>
            <dt>任务状态</dt>
            <dd>{{ latestTask.status }}</dd>
          </div>
          <div>
            <dt>原始视频</dt>
            <dd>{{ latestTask.source_uri }}</dd>
          </div>
          <div>
            <dt>结果视频</dt>
            <dd>{{ latestTask.output_uri ?? "分析完成后生成" }}</dd>
          </div>
        </dl>

        <div class="task-list">
          <h3>历史任务</h3>
          <div v-for="task in taskHistory" :key="task.id" class="task-row">
            <span>{{ task.name }}</span>
            <small>{{ task.time }}</small>
            <b :class="`state-${task.status}`">{{ task.status }}</b>
          </div>
        </div>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { Download, ExternalLink, Film, FolderOpen, Rocket, UploadCloud } from "lucide-vue-next";

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

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const selectedExercise = ref("squat");
const isDragging = ref(false);
const uploadState = ref<"idle" | "ready" | "uploading" | "success" | "failed">("idle");
const message = ref("");
const latestTask = ref<AnalysisTask | null>(null);
const localPreviewUrl = ref("");

const taskHistory = [
  { id: "t1", name: "深蹲训练视频", time: "今天 14:10", status: "success" },
  { id: "t2", name: "俯卧撑训练视频", time: "昨天 19:22", status: "failed" },
  { id: "t3", name: "开合跳训练视频", time: "昨天 18:05", status: "pending" }
];

const outputVideoUrl = computed(() => {
  if (!latestTask.value?.output_uri) {
    return "";
  }
  return `/api/files/${encodeFilePath(latestTask.value.output_uri)}`;
});

const progress = computed(() => {
  if (uploadState.value === "uploading") return 68;
  if (uploadState.value === "success") return 100;
  if (uploadState.value === "failed") return 18;
  return selectedFile.value ? 12 : 0;
});

const taskLabel = computed(() => {
  if (uploadState.value === "uploading") return "running";
  if (uploadState.value === "success") return "success";
  if (uploadState.value === "failed") return "failed";
  return selectedFile.value ? "pending" : "idle";
});

const statusClass = computed(() => (taskLabel.value === "success" ? "good" : taskLabel.value === "failed" ? "danger" : "idle"));

const helperText = computed(() => {
  if (uploadState.value === "success") {
    return "分析完成，右侧已生成输出视频展示窗口。";
  }
  if (selectedFile.value) {
    return "视频已选择，开始分析后会上传到后端并生成结果视频。";
  }
  return "支持 mp4、avi、mov。分析过程可能需要几十秒，请等待输出窗口更新。";
});

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
    message.value = "请选择 mp4、avi 或 mov 格式的视频文件。";
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
  latestTask.value = null;
  message.value = "正在上传视频并生成输出视频，请稍候...";

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
    message.value = "上传失败，请确认后端服务已启动。";
  }
}
</script>
