<template>
  <div class="page realtime-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime Training</p>
        <h1>{{ store.currentExerciseMeta.name }}实时检测</h1>
        <p class="subtle">训练中实时接收关键点、阶段、次数、评分与错误提示。</p>
      </div>
      <div class="header-actions">
        <span class="status-pill" :class="cameraActive ? 'good' : 'idle'">
          {{ cameraActive ? "摄像头正常" : "等待摄像头" }}
        </span>
        <button class="primary-button" type="button" @click="connectCamera">
          <Camera :size="18" />
          {{ cameraActive ? "已连接" : "连接摄像头" }}
        </button>
      </div>
    </header>

    <section class="training-cockpit">
      <div class="camera-panel">
        <video
          v-show="cameraActive"
          ref="videoRef"
          autoplay
          muted
          playsinline
          class="camera-video"
        ></video>
        <SkeletonCanvas v-if="!cameraActive" />
      </div>

      <aside class="metric-rail">
        <div>
          <p class="eyebrow">Live Metrics</p>
          <h2>实时数据面板</h2>
        </div>
        <MetricTile label="当前动作" :value="store.currentExerciseMeta.name" :hint="store.currentExerciseMeta.category" />
        <MetricTile label="阶段" :value="store.stage" hint="WebSocket stage" />
        <MetricTile label="次数" :value="store.count" hint="total count" />
        <MetricTile label="有效次数" :value="store.validCount" hint="valid count" />
        <MetricTile label="评分" :value="store.score" hint="score" />

        <div v-if="cameraError" class="alert-line danger">{{ cameraError }}</div>
        <div class="error-stack">
          <strong>错误提示</strong>
          <span v-for="error in store.errors" :key="error">{{ error }}</span>
        </div>
      </aside>
    </section>

    <section class="control-bar">
      <button class="primary-button" type="button">
        <Play :size="18" />
        开始
      </button>
      <button class="secondary-button" type="button">
        <Pause :size="18" />
        暂停
      </button>
      <button class="secondary-button" type="button">
        <RefreshCcw :size="18" />
        重新检测
      </button>
      <button class="secondary-button" type="button">
        <Save :size="18" />
        保存记录
      </button>
      <button class="secondary-button" type="button">
        <FileSearch :size="18" />
        查看本次详情
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Camera, FileSearch, Pause, Play, RefreshCcw, Save } from "lucide-vue-next";

import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";
import { useTrainingStore } from "../stores/training";

const store = useTrainingStore();
const videoRef = ref<HTMLVideoElement | null>(null);
const cameraActive = ref(false);
const cameraError = ref("");

async function connectCamera() {
  cameraError.value = "";

  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = "当前浏览器不支持摄像头访问。";
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: false
    });

    if (videoRef.value) {
      videoRef.value.srcObject = stream;
      cameraActive.value = true;
    }
  } catch {
    cameraError.value = "摄像头连接失败，请检查浏览器权限。";
  }
}
</script>
