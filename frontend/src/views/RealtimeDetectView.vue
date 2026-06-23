<template>
  <div class="page realtime-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime Training</p>
        <h1>{{ store.currentExerciseMeta.name }}实时检测</h1>
        <p class="subtle">训练中实时接收关键点、阶段、次数、评分与错误提示。</p>
      </div>
      <div class="header-actions">
        <span class="status-pill" :class="connectionClass">{{ statusLabel }}</span>
        <button class="primary-button" type="button" @click="connectCamera">
          <Camera :size="18" />
          {{ cameraActive ? "摄像头已连接" : "连接摄像头" }}
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
        <div v-if="savedMessage" class="alert-line">{{ savedMessage }}</div>
        <div class="error-stack">
          <strong>错误提示</strong>
          <span v-if="store.errors.length === 0">暂无错误</span>
          <span v-for="error in store.errors" :key="error">{{ error }}</span>
        </div>
      </aside>
    </section>

    <section class="control-bar">
      <button class="primary-button" type="button" :disabled="trainingState === 'running'" @click="startTraining">
        <Play :size="18" />
        开始
      </button>
      <button class="secondary-button" type="button" :disabled="!canPause" @click="togglePause">
        <Pause :size="18" />
        {{ trainingState === "paused" ? "继续" : "暂停" }}
      </button>
      <button class="secondary-button" type="button" @click="resetTraining">
        <RefreshCcw :size="18" />
        重新检测
      </button>
      <button class="secondary-button" type="button" :disabled="!canSave" @click="finishTraining">
        <Save :size="18" />
        保存记录
      </button>
      <button class="secondary-button" type="button" :disabled="!lastSessionId" @click="viewSession">
        <FileSearch :size="18" />
        查看本次详情
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";
import { Camera, FileSearch, Pause, Play, RefreshCcw, Save } from "lucide-vue-next";

import { apiWebSocketUrl } from "../api/client";
import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";
import { useTrainingStore } from "../stores/training";

type TrainingState = "idle" | "connecting" | "running" | "paused" | "finished" | "error";
type Keypoint = { x: number; y: number; visibility: number };
type Keypoints = Record<string, Keypoint>;

const router = useRouter();
const store = useTrainingStore();
const videoRef = ref<HTMLVideoElement | null>(null);
const cameraActive = ref(false);
const cameraError = ref("");
const savedMessage = ref("");
const trainingState = ref<TrainingState>("idle");
const lastSessionId = ref("");

let socket: WebSocket | null = null;
let frameTimer: ReturnType<typeof setInterval> | null = null;
let sampleStep = 0;

const statusLabel = computed(() => {
  const labels: Record<TrainingState, string> = {
    idle: cameraActive.value ? "摄像头就绪" : "等待摄像头",
    connecting: "正在连接",
    running: "训练中",
    paused: "已暂停",
    finished: "已保存",
    error: "连接异常"
  };
  return labels[trainingState.value];
});

const connectionClass = computed(() => {
  if (trainingState.value === "running" || trainingState.value === "finished") return "good";
  if (trainingState.value === "error") return "danger";
  return "idle";
});

const canPause = computed(() => trainingState.value === "running" || trainingState.value === "paused");
const canSave = computed(() => trainingState.value === "running" || trainingState.value === "paused");

async function connectCamera() {
  cameraError.value = "";

  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = "当前浏览器不支持摄像头访问。";
    trainingState.value = "error";
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

    await openRealtimeSocket();
  } catch {
    cameraError.value = "摄像头或实时通道连接失败，请检查浏览器权限和后端服务。";
    trainingState.value = "error";
  }
}

async function startTraining() {
  savedMessage.value = "";
  lastSessionId.value = "";
  store.resetLiveMetrics();

  if (!cameraActive.value) {
    await connectCamera();
  } else {
    await openRealtimeSocket();
  }

  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  trainingState.value = "connecting";
  socket.send(JSON.stringify({ type: "start", exercise: store.currentExercise }));
}

function togglePause() {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  if (trainingState.value === "running") {
    stopFrameLoop();
    socket.send(JSON.stringify({ type: "pause" }));
    return;
  }

  if (trainingState.value === "paused") {
    socket.send(JSON.stringify({ type: "resume" }));
  }
}

function resetTraining() {
  stopFrameLoop();
  sampleStep = 0;
  savedMessage.value = "";
  lastSessionId.value = "";
  store.resetLiveMetrics();

  if (socket?.readyState === WebSocket.OPEN) {
    trainingState.value = "connecting";
    socket.send(JSON.stringify({ type: "start", exercise: store.currentExercise }));
  } else {
    trainingState.value = cameraActive.value ? "idle" : "idle";
  }
}

function finishTraining() {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  stopFrameLoop();
  socket.send(JSON.stringify({ type: "finish" }));
}

function viewSession() {
  router.push({ path: "/sessions", query: { session: lastSessionId.value } });
}

function openRealtimeSocket(): Promise<void> {
  if (socket?.readyState === WebSocket.OPEN) {
    return Promise.resolve();
  }

  closeSocket();
  trainingState.value = "connecting";

  return new Promise((resolve, reject) => {
    socket = new WebSocket(apiWebSocketUrl("/realtime/pose"));

    socket.onopen = () => resolve();
    socket.onerror = () => {
      cameraError.value = "实时检测通道连接失败，请确认后端服务已启动。";
      trainingState.value = "error";
      reject(new Error("WebSocket connection failed"));
    };
    socket.onclose = () => {
      stopFrameLoop();
      if (trainingState.value === "running" || trainingState.value === "connecting") {
        trainingState.value = "error";
      }
    };
    socket.onmessage = (event) => handleRealtimeMessage(JSON.parse(event.data));
  });
}

function handleRealtimeMessage(message: Record<string, any>) {
  if (message.type === "status") {
    if (message.state === "running") {
      trainingState.value = "running";
      startFrameLoop();
    } else if (message.state === "paused") {
      trainingState.value = "paused";
      stopFrameLoop();
    }
    return;
  }

  if (message.type === "analysis") {
    store.updateLiveMetrics({
      stage: String(message.stage),
      count: Number(message.count ?? 0),
      valid_count: Number(message.valid_count ?? 0),
      score: Number(message.score ?? 0),
      errors: Array.isArray(message.errors) ? message.errors : []
    });
    return;
  }

  if (message.type === "summary") {
    trainingState.value = "finished";
    stopFrameLoop();
    const session = message.session as { session_id?: string; total_count?: number } | undefined;
    lastSessionId.value = session?.session_id ?? "";
    savedMessage.value = session?.session_id
      ? `记录已保存，共 ${session.total_count ?? store.count} 次。`
      : "本次没有完成动作，未生成训练记录。";
  }
}

function startFrameLoop() {
  stopFrameLoop();
  sendFrame();
  frameTimer = setInterval(sendFrame, 520);
}

function stopFrameLoop() {
  if (frameTimer) {
    clearInterval(frameTimer);
    frameTimer = null;
  }
}

function sendFrame() {
  if (!socket || socket.readyState !== WebSocket.OPEN || trainingState.value !== "running") return;

  socket.send(JSON.stringify({
    type: "frame",
    exercise: store.currentExercise,
    timestamp: Date.now(),
    keypoints: createSquatSampleKeypoints(sampleStep++)
  }));
}

function createSquatSampleKeypoints(step: number): Keypoints {
  const down = step % 2 === 0;
  const hipY = down ? 0.72 : 0.24;
  const kneeY = down ? 0.66 : 0.58;

  return {
    left_hip: { x: 0.45, y: hipY, visibility: 0.99 },
    left_knee: { x: 0.47, y: kneeY, visibility: 0.99 },
    left_ankle: { x: 0.47, y: 0.82, visibility: 0.99 },
    right_hip: { x: 0.55, y: hipY, visibility: 0.99 },
    right_knee: { x: 0.53, y: kneeY, visibility: 0.99 },
    right_ankle: { x: 0.53, y: 0.82, visibility: 0.99 }
  };
}

function closeSocket() {
  stopFrameLoop();
  if (socket) {
    socket.onclose = null;
    socket.close();
    socket = null;
  }
}

onBeforeUnmount(() => {
  closeSocket();
  const stream = videoRef.value?.srcObject as MediaStream | null;
  stream?.getTracks().forEach((track) => track.stop());
});
</script>
