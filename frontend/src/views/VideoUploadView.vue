<template>
  <div class="page narrow">
    <header class="page-header">
      <div>
        <p class="eyebrow">Async Analysis</p>
        <h1>视频上传分析</h1>
      </div>
    </header>

    <section
      class="upload-zone"
      :class="{ active: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <UploadCloud :size="42" />
      <strong>{{ selectedFile ? selectedFile.name : "拖入训练视频或点击选择" }}</strong>
      <span>{{ helperText }}</span>

      <input
        ref="fileInput"
        class="hidden-input"
        type="file"
        accept="video/mp4,video/avi,video/quicktime,.mp4,.avi,.mov"
        @change="handleFileChange"
      />

      <div class="upload-actions">
        <button class="primary-button" @click="openFilePicker">选择视频</button>
        <button
          class="secondary-button"
          :disabled="!selectedFile || uploadState === 'uploading'"
          @click="uploadVideo"
        >
          {{ uploadState === "uploading" ? "上传中..." : "开始分析" }}
        </button>
      </div>

      <div v-if="message" class="alert-line" :class="{ danger: uploadState === 'failed' }">
        {{ message }}
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { UploadCloud } from "lucide-vue-next";

import { apiUpload } from "../api/client";

interface UploadResponse {
  file_uri: string;
  task: {
    task_id: string;
    exercise: string;
    source_uri: string;
    status: string;
  };
}

const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const isDragging = ref(false);
const uploadState = ref<"idle" | "ready" | "uploading" | "success" | "failed">("idle");
const message = ref("");

const helperText = computed(() => {
  if (uploadState.value === "success") {
    return "视频已进入分析队列，可以在任务状态中查看进度。";
  }
  if (selectedFile.value) {
    return "已选择视频，点击开始分析后会上传到后端并创建异步任务。";
  }
  return "上传后进入 Celery 队列，Worker 后台分析并生成结果视频。";
});

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
  if (!file) {
    return;
  }

  if (!file.type.startsWith("video/") && !/\.(mp4|avi|mov)$/i.test(file.name)) {
    uploadState.value = "failed";
    message.value = "请选择 mp4、avi 或 mov 格式的视频文件";
    return;
  }

  selectedFile.value = file;
  uploadState.value = "ready";
  message.value = `已选择：${file.name}`;
}

async function uploadVideo() {
  if (!selectedFile.value) {
    message.value = "请先选择一个训练视频";
    return;
  }

  uploadState.value = "uploading";
  message.value = "正在上传视频并创建分析任务...";

  const formData = new FormData();
  formData.append("exercise", "squat");
  formData.append("file", selectedFile.value);

  try {
    const result = await apiUpload<UploadResponse>("/videos/upload", formData);
    uploadState.value = "success";
    message.value = `任务已创建：${result.task.task_id}（状态：${result.task.status}）`;
  } catch {
    uploadState.value = "failed";
    message.value = "上传失败，请确认后端服务 http://localhost:8000 已启动";
  }
}
</script>
