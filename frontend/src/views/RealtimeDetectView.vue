<template>
  <div class="page realtime-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime Training</p>
        <h1>{{ store.currentExerciseMeta.name }}实时检测</h1>
        <p class="subtle">摄像头或测试视频画面实时叠加人体骨架，并同步返回阶段、次数、评分与纠错提示。</p>
      </div>
      <div class="header-actions">
        <span class="status-pill" :class="connectionClass">{{ statusLabel }}</span>
        <button class="primary-button" type="button" @click="connectCamera">
          <Camera :size="18" />
          {{ cameraActive ? "摄像头已连接" : "连接摄像头" }}
        </button>
        <button class="secondary-button" type="button" :disabled="videoTestLoading" @click="openVideoTestPicker">
          <UploadCloud :size="18" />
          {{ videoTestLoading ? "视频检测中..." : "视频测试" }}
        </button>
        <input
          ref="videoTestInput"
          class="hidden-input"
          type="file"
          accept="video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov"
          @change="handleVideoTestFile"
        />
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
        <canvas v-show="cameraActive" ref="overlayRef" class="pose-overlay" aria-label="实时人体骨架"></canvas>
        <div v-if="cameraActive && poseStatus" class="pose-status">{{ poseStatus }}</div>
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

        <div class="live-data-panel">
          <div class="live-data-header">
            <strong>参考模板</strong>
            <span>{{ selectedTemplate?.source === "builtin" ? "内置" : "自定义" }}</span>
          </div>
          <select v-model="selectedTemplateId" class="template-select" @change="handleTemplateChange">
            <option value="" disabled>请选择参考模板</option>
            <option
              v-for="template in templateOptions"
              :key="template.template_id"
              :value="template.template_id"
            >
              {{ template.name }} 路 {{ template.view }} 路 {{ template.version }}
            </option>
          </select>
          <small v-if="selectedTemplate">
            {{ selectedTemplate.valid_frames || "榛樿" }} 甯у弬鑰冩洸绾?          </small>
        </div>

        <div class="live-data-panel">
          <div class="live-data-header">
            <strong>实时角度</strong>
            <span>{{ currentMetrics ? "更新中" : "等待帧数据" }}</span>
          </div>
          <div class="angle-grid">
            <div>
              <span>膝角</span>
              <strong>{{ formatAngle(currentMetrics?.knee_angle) }}</strong>
            </div>
            <div>
              <span>髋角</span>
              <strong>{{ formatAngle(currentMetrics?.hip_angle) }}</strong>
            </div>
            <div>
              <span>躯干</span>
              <strong>{{ formatAngle(currentMetrics?.trunk_angle) }}</strong>
            </div>
            <div>
              <span>对称差</span>
              <strong>{{ formatAngle(currentMetrics?.knee_symmetry_diff) }}</strong>
            </div>
          </div>
        </div>

        <div class="live-data-panel">
          <div class="live-data-header">
            <strong>模板相似度</strong>
            <span>{{ displayTemplateScore?.is_partial ? "动态参考" : "完整评分" }}</span>
          </div>
          <div class="live-score-row">
            <span>鍔ㄦ€佹€诲垎</span>
            <strong>{{ formatScore(displayTemplateScore?.score) }}</strong>
          </div>
          <div class="angle-diff-list">
            <div>
              <span>膝角</span>
              <b>{{ formatAngle(currentMetrics?.knee_angle) }}</b>
              <b>{{ formatAngle(displayTemplateScore?.differences.knee_angle) }}</b>
              <b>{{ formatScore(displayTemplateScore?.detail_scores.knee_angle) }}</b>
            </div>
            <div>
              <span>髋角</span>
              <b>{{ formatAngle(currentMetrics?.hip_angle) }}</b>
              <b>{{ formatAngle(displayTemplateScore?.differences.hip_angle) }}</b>
              <b>{{ formatScore(displayTemplateScore?.detail_scores.hip_angle) }}</b>
            </div>
            <div>
              <span>躯干</span>
              <b>{{ formatAngle(currentMetrics?.trunk_angle) }}</b>
              <b>{{ formatAngle(displayTemplateScore?.differences.trunk_angle) }}</b>
              <b>{{ formatScore(displayTemplateScore?.detail_scores.trunk_angle) }}</b>
            </div>
            <div>
              <span>对称差</span>
              <b>{{ formatAngle(currentMetrics?.knee_symmetry_diff) }}</b>
              <b>{{ formatAngle(displayTemplateScore?.differences.knee_symmetry_diff) }}</b>
              <b>{{ formatScore(displayTemplateScore?.detail_scores.knee_symmetry_diff) }}</b>
            </div>
          </div>
          <div class="angle-diff-legend">
            <span>当前</span>
            <span>误差</span>
            <span>细项分</span>
          </div>
        </div>

        <div v-if="cameraError" class="alert-line danger">{{ cameraError }}</div>
        <div v-if="savedMessage" class="alert-line">{{ savedMessage }}</div>
        <div class="error-stack">
          <strong>閿欒鎻愮ず</strong>
          <span v-if="store.errors.length === 0">暂无错误</span>
          <span v-for="error in store.errors" :key="error">{{ error }}</span>
        </div>

        <!-- 模板评分结果 -->
        <div v-if="templateScore" class="template-score-panel">
          <div class="template-score-header">
            <strong>模板评分</strong>
            <span class="template-score-level" :class="templateScore.level">{{ templateScore.level }}</span>
          </div>
          <div class="template-score-total">
            <span class="template-score-value">{{ templateScore.score.toFixed(1) }}</span>
            <span class="template-score-label">总分</span>
          </div>
          <div class="template-score-details">
            <div class="detail-item">
              <span class="detail-label">膝关节角度</span>
              <span class="detail-value">{{ templateScore.detail_scores.knee_angle.toFixed(1) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">髋关节角度</span>
              <span class="detail-value">{{ templateScore.detail_scores.hip_angle.toFixed(1) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">躯干角度</span>
              <span class="detail-value">{{ templateScore.detail_scores.trunk_angle.toFixed(1) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">左右对称性</span>
              <span class="detail-value">{{ templateScore.detail_scores.knee_symmetry_diff.toFixed(1) }}</span>
            </div>
          </div>
          <div v-if="templateScore.errors.length > 0" class="template-errors">
            <strong>主要问题：</strong>
            <span v-for="error in templateScore.errors" :key="error" class="error-item">{{ error }}</span>
          </div>
          <div v-if="templateScore.suggestions.length > 0" class="template-suggestions">
            <strong>改进建议：</strong>
            <span v-for="suggestion in templateScore.suggestions" :key="suggestion" class="suggestion-item">{{ suggestion }}</span>
          </div>
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
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Camera, FileSearch, Pause, Play, RefreshCcw, Save, UploadCloud } from "lucide-vue-next";

import { apiGet, apiUpload, apiWebSocketUrl, apiPost } from "../api/client";
import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";
import {
  clearPoseCanvas,
  createPoseLandmarker,
  detectPose,
  drawPose,
  drawPoseFromKeypoints,
  type BackendKeypoints,
  toBackendKeypoints,
} from "../services/poseLandmarker";
import { useTrainingStore } from "../stores/training";

type TrainingState = "idle" | "connecting" | "running" | "paused" | "finished" | "error";
type PoseLandmarkerInstance = Awaited<ReturnType<typeof createPoseLandmarker>>;

type SquatMetrics = {
  knee_angle: number;
  hip_angle: number;
  trunk_angle: number;
  knee_symmetry_diff: number;
};

type TemplateScore = {
  action?: string;
  template_id?: string;
  is_partial?: boolean;
  score: number;
  level: string;
  detail_scores: SquatMetrics;
  differences: SquatMetrics;
  errors: string[];
  suggestions: string[];
};

type TemplateOption = {
  template_id: string;
  name: string;
  action: string;
  view: string;
  version: string;
  valid_frames: number;
  source?: string;
};

type VideoTestFrame = {
  frame_index: number;
  stage: string;
  count: number;
  valid_count: number;
  score: number;
  errors: string[];
  keypoints?: BackendKeypoints;
  metrics?: SquatMetrics;
};

type VideoTestResponse = {
  exercise: string;
  processed_frames: number;
  video_width: number;
  video_height: number;
  frames: VideoTestFrame[];
  summary: {
    total_count: number;
    valid_count: number;
    error_count: number;
    average_score: number;
  };
  template_score?: TemplateScore;
};

const SEND_INTERVAL_MS = 100;
const VIDEO_TEST_PLAYBACK_MS = 100;
const DYNAMIC_SCORE_MIN_FRAMES = 10;
const DYNAMIC_SCORE_INTERVAL_MS = 500;

const router = useRouter();
const store = useTrainingStore();
const videoRef = ref<HTMLVideoElement | null>(null);
const overlayRef = ref<HTMLCanvasElement | null>(null);
const videoTestInput = ref<HTMLInputElement | null>(null);
const cameraActive = ref(false);
const cameraError = ref("");
const poseStatus = ref("");
const savedMessage = ref("");
const videoTestLoading = ref(false);
const trainingState = ref<TrainingState>("idle");
const lastSessionId = ref("");
const currentMetrics = ref<SquatMetrics | null>(null);
const liveTemplateScore = ref<TemplateScore | null>(null);
const templateScore = ref<TemplateScore | null>(null);
const templateOptions = ref<TemplateOption[]>([]);
const selectedTemplateId = ref("");
const lastDynamicScoreAt = ref(0);
const dynamicScoreInFlight = ref(false);

let socket: WebSocket | null = null;
let poseLandmarker: PoseLandmarkerInstance | null = null;
let animationFrameId: number | null = null;
let videoTestTimer: ReturnType<typeof setInterval> | null = null;
let videoTestUrl = "";
let lastSentAt = 0;
let motionFrames: SquatMetrics[] = [];

const statusLabel = computed(() => {
  const labels: Record<TrainingState, string> = {
    idle: cameraActive.value ? "视频源就绪" : "等待视频源",
    connecting: "正在连接",
    running: "训练中",
    paused: "已暂停",
    finished: "已完成",
    error: "连接异常",
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
const displayTemplateScore = computed(() => liveTemplateScore.value ?? templateScore.value);
const selectedTemplate = computed(() =>
  templateOptions.value.find((template) => template.template_id === selectedTemplateId.value)
);

function formatAngle(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)}°` : "--";
}

function formatScore(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "--";
}

async function loadTemplateOptions() {
  if (store.currentExercise !== "squat") return;

  try {
    const response = await apiGet<{ items: TemplateOption[] }>(`/exercises/${store.currentExercise}/templates`);
    templateOptions.value = response.items;
    if (!selectedTemplateId.value && response.items.length > 0) {
      selectedTemplateId.value = response.items[0].template_id;
    }
  } catch (error) {
    console.error("加载模板列表失败:", error);
  }
}

function handleTemplateChange() {
  resetDynamicTemplateState();
}

async function connectCamera() {
  cameraError.value = "";
  poseStatus.value = "正在加载姿态识别模型...";

  if (!navigator.mediaDevices?.getUserMedia) {
    cameraError.value = "当前浏览器不支持摄像头访问。";
    poseStatus.value = "";
    trainingState.value = "error";
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: 1280, height: 720 },
      audio: false,
    });

    if (videoRef.value) {
      revokeVideoTestUrl();
      videoRef.value.removeAttribute("src");
      videoRef.value.srcObject = stream;
      videoRef.value.loop = false;
      cameraActive.value = true;
    }

    poseLandmarker = await createPoseLandmarker();
    poseStatus.value = "模型已就绪，请站入画面后开始训练";
    await openRealtimeSocket();
  } catch {
    cameraError.value = "摄像头、姿态识别模型或实时通道连接失败，请检查浏览器权限和后端服务。";
    poseStatus.value = "";
    trainingState.value = "error";
  }
}

async function startTraining() {
  savedMessage.value = "";
  lastSessionId.value = "";
  poseStatus.value = "";
  store.resetLiveMetrics();
  resetDynamicTemplateState(true);
  clearPoseCanvas(overlayRef.value);
  stopVideoTestPlayback();

  if (!cameraActive.value || !poseLandmarker) {
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
    stopPoseLoop();
    socket.send(JSON.stringify({ type: "pause" }));
    return;
  }

  if (trainingState.value === "paused") {
    socket.send(JSON.stringify({ type: "resume" }));
  }
}

function resetTraining() {
  stopPoseLoop();
  stopVideoTestPlayback();
  lastSentAt = 0;
  savedMessage.value = "";
  lastSessionId.value = "";
  poseStatus.value = "";
  store.resetLiveMetrics();
  resetDynamicTemplateState(true);
  clearPoseCanvas(overlayRef.value);

  if (socket?.readyState === WebSocket.OPEN) {
    trainingState.value = "connecting";
    socket.send(JSON.stringify({ type: "start", exercise: store.currentExercise }));
  } else {
    trainingState.value = "idle";
  }
}

function finishTraining() {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  stopPoseLoop();
  stopVideoTestPlayback();
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
      stopPoseLoop();
      if (trainingState.value === "running" || trainingState.value === "connecting") {
        trainingState.value = "error";
      }
    };
    socket.onmessage = (event) => handleRealtimeMessage(JSON.parse(event.data));
  });
}

function handleRealtimeMessage(message: Record<string, any>) {
  console.log("鏀跺埌娑堟伅:", message);

  if (message.type === "status") {
    console.log("鐘舵€佹秷鎭?", message.state);
    if (message.state === "running") {
      trainingState.value = "running";
      poseStatus.value = "开始检测...";
      resetDynamicTemplateState(true);
      startPoseLoop();
    } else if (message.state === "paused") {
      trainingState.value = "paused";
      stopPoseLoop();
    }
    return;
  }

  if (message.type === "analysis") {
    handleAnalysisFrame(message as VideoTestFrame);
    return;
  }

  if (message.type === "summary") {
    trainingState.value = "finished";
    stopPoseLoop();
    poseStatus.value = "";

    // 调用模板评分
    if (motionFrames.length > 0 && store.currentExercise === "squat") {
      scoreByTemplate();
    }

    const session = message.session as { session_id?: string; total_count?: number } | undefined;
    lastSessionId.value = session?.session_id ?? "";
    savedMessage.value = session?.session_id
      ? `记录已保存，共 ${session.total_count ?? store.count} 次。`
      : "本次没有完成动作，未生成训练记录。";
  }
}

function startPoseLoop() {
  stopVideoTestPlayback();
  stopPoseLoop();
  lastSentAt = 0;
  animationFrameId = window.requestAnimationFrame(runPoseFrame);
}

function stopPoseLoop() {
  if (animationFrameId !== null) {
    window.cancelAnimationFrame(animationFrameId);
    animationFrameId = null;
  }
}

function runPoseFrame(timestamp: number) {
  if (trainingState.value !== "running") return;

  const video = videoRef.value;
  const canvas = overlayRef.value;

  if (!video || !canvas || !poseLandmarker || !socket || socket.readyState !== WebSocket.OPEN) {
    animationFrameId = window.requestAnimationFrame(runPoseFrame);
    return;
  }

  const landmarks = detectPose(poseLandmarker, video, timestamp);
  drawPose(canvas, landmarks);

  if (!landmarks) {
    poseStatus.value = "鏈娴嬪埌浜轰綋锛岃绔欏叆鐢婚潰";
  } else {
    poseStatus.value = "";
    if (timestamp - lastSentAt >= SEND_INTERVAL_MS) {
      lastSentAt = timestamp;
      socket.send(JSON.stringify({
        type: "frame",
        exercise: store.currentExercise,
        timestamp: Date.now(),
        keypoints: toBackendKeypoints(landmarks),
      }));
    }
  }

  if (videoTestUrl && video.duration > 0 && video.currentTime >= video.duration) {
    finishTraining();
    return;
  }

  animationFrameId = window.requestAnimationFrame(runPoseFrame);
}

function openVideoTestPicker() {
  videoTestInput.value?.click();
}

async function handleVideoTestFile(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;

  stopPoseLoop();
  stopVideoTestPlayback();
  closeSocket();
  clearPoseCanvas(overlayRef.value);
  store.resetLiveMetrics();
  resetDynamicTemplateState(true);
  savedMessage.value = "";
  lastSessionId.value = "";
  cameraError.value = "";
  poseStatus.value = "姝ｅ湪鍔犺浇濮挎€佽瘑鍒ā鍨?..";
  videoTestLoading.value = true;
  trainingState.value = "connecting";

  try {
    if (!poseLandmarker) {
      poseLandmarker = await createPoseLandmarker();
      poseStatus.value = "模型已就绪，正在连接实时检测通道...";
    }

    await openRealtimeSocket();

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      throw new Error("无法连接到实时检测通道");
    }

    poseStatus.value = "连接成功，正在加载视频...";
    showVideoTestPreview(file);

    socket.send(JSON.stringify({ type: "start", exercise: store.currentExercise }));
  } catch (error) {
    console.error("视频测试失败:", error);
    cameraError.value = "视频测试失败，请确认后端服务已启动且视频格式可读。";
    poseStatus.value = "";
    trainingState.value = "error";
  } finally {
    videoTestLoading.value = false;
  }
}

function showVideoTestPreview(file: File) {
  revokeVideoTestUrl();
  videoTestUrl = URL.createObjectURL(file);

  if (videoRef.value) {
    const stream = videoRef.value.srcObject as MediaStream | null;
    stream?.getTracks().forEach((track) => track.stop());
    videoRef.value.srcObject = null;
    videoRef.value.src = videoTestUrl;
    videoRef.value.loop = false;
    videoRef.value.currentTime = 0;
    videoRef.value.play().catch(() => undefined);
  }

  cameraActive.value = true;
}

function playVideoTestResult(result: VideoTestResponse) {
  if (result.frames.length === 0) {
    poseStatus.value = "视频没有产生可用的实时检测帧";
    trainingState.value = "finished";
    return;
  }

  let frameIndex = 0;
  trainingState.value = "running";
  poseStatus.value = "姝ｅ湪鎸夊疄鏃惰妭濂忔挱鏀捐棰戞娴嬬粨鏋?..";

  videoTestTimer = setInterval(() => {
    const frame = result.frames[frameIndex];
    handleAnalysisFrame(frame);

    if (overlayRef.value && frame.keypoints) {
      drawPoseFromKeypoints(overlayRef.value, frame.keypoints, result.video_width, result.video_height);
    }

    frameIndex += 1;
    if (frameIndex >= result.frames.length) {
      stopVideoTestPlayback();
      trainingState.value = "finished";
      poseStatus.value = "";
      void scoreByTemplate("final");
      savedMessage.value = "视频测试完成，共检测 " + result.processed_frames + " 帧，计数 " + result.summary.total_count + " 次。";
    }
  }, VIDEO_TEST_PLAYBACK_MS);
}

function resetDynamicTemplateState(clearMetrics = false) {
  motionFrames = [];
  liveTemplateScore.value = null;
  templateScore.value = null;
  lastDynamicScoreAt.value = 0;
  dynamicScoreInFlight.value = false;

  if (clearMetrics) {
    currentMetrics.value = null;
  }
}

function handleAnalysisFrame(frame: VideoTestFrame) {
  updateMetricsFromFrame(frame);

  if (!frame.metrics || store.currentExercise !== "squat") return;

  const metrics: SquatMetrics = {
    knee_angle: Number(frame.metrics.knee_angle),
    hip_angle: Number(frame.metrics.hip_angle),
    trunk_angle: Number(frame.metrics.trunk_angle),
    knee_symmetry_diff: Number(frame.metrics.knee_symmetry_diff),
  };

  currentMetrics.value = metrics;
  motionFrames.push(metrics);
  requestDynamicTemplateScore();
}

function requestDynamicTemplateScore() {
  if (motionFrames.length < DYNAMIC_SCORE_MIN_FRAMES) return;
  if (dynamicScoreInFlight.value) return;

  const now = Date.now();
  if (now - lastDynamicScoreAt.value < DYNAMIC_SCORE_INTERVAL_MS) return;

  lastDynamicScoreAt.value = now;
  void scoreByTemplate("live");
}

async function scoreByTemplate(mode: "live" | "final" = "final") {
  if (motionFrames.length < 2 || store.currentExercise !== "squat") return;

  if (mode === "live") {
    dynamicScoreInFlight.value = true;
  }

  try {
    const response = await apiPost<TemplateScore>("/realtime/score-action", {
      action: "squat",
      template_id: selectedTemplateId.value || undefined,
      frames: motionFrames,
    });

    if (mode === "live") {
      liveTemplateScore.value = response;
    } else {
      templateScore.value = response;
      liveTemplateScore.value = response;
    }
    console.log("模板评分结果:", response);
  } catch (error) {
    console.error("模板评分失败:", error);
  } finally {
    if (mode === "live") {
      dynamicScoreInFlight.value = false;
    }
  }
}

function updateMetricsFromFrame(frame: VideoTestFrame) {
  store.updateLiveMetrics({
    stage: String(frame.stage),
    count: Number(frame.count ?? 0),
    valid_count: Number(frame.valid_count ?? 0),
    score: Number(frame.score ?? 0),
    errors: Array.isArray(frame.errors) ? frame.errors : [],
  });
}

function stopVideoTestPlayback() {
  if (videoTestTimer) {
    clearInterval(videoTestTimer);
    videoTestTimer = null;
  }
}

function closeSocket() {
  stopPoseLoop();
  if (socket) {
    socket.onclose = null;
    socket.close();
    socket = null;
  }
}

function revokeVideoTestUrl() {
  if (videoTestUrl) {
    URL.revokeObjectURL(videoTestUrl);
    videoTestUrl = "";
  }
}

onMounted(() => {
  void loadTemplateOptions();
});

onBeforeUnmount(() => {
  closeSocket();
  stopVideoTestPlayback();
  clearPoseCanvas(overlayRef.value);
  const stream = videoRef.value?.srcObject as MediaStream | null;
  stream?.getTracks().forEach((track) => track.stop());
  revokeVideoTestUrl();
});
</script>
