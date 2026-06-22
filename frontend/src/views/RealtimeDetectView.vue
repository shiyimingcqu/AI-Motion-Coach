<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime</p>
        <h1>摄像头实时检测</h1>
      </div>
      <button class="primary-button" @click="connectCamera">
        {{ cameraActive ? "摄像头已连接" : "连接摄像头" }}
      </button>
    </header>

    <section class="operations-grid">
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
      <div class="panel">
        <h2>实时反馈</h2>
        <div class="feedback-list">
          <MetricTile label="当前动作" value="深蹲" hint="squat" />
          <MetricTile label="次数" :value="store.count" hint="total count" />
          <MetricTile label="有效次数" :value="store.validCount" hint="valid count" />
          <MetricTile label="评分" :value="store.score" hint="score" />
        </div>
        <div v-if="cameraError" class="alert-line danger">{{ cameraError }}</div>
        <div class="alert-line">{{ store.errors[0] }}</div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

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
    cameraError.value = "当前浏览器不支持摄像头访问";
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
    cameraError.value = "摄像头连接失败，请检查浏览器权限";
  }
}
</script>
