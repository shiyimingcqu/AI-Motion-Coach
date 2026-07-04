<template>
  <div class="page realtime-page">
    <div v-if="finishPending" class="finish-overlay" role="dialog" aria-modal="true" aria-label="结束训练中">
      <div class="finish-modal">
        <div class="finish-spinner" aria-hidden="true"></div>
        <strong>正在结束训练</strong>
        <p>{{ finishStatusText }}</p>
      </div>
    </div>
    <header class="page-header">
      <div>
        <p class="eyebrow">Realtime Training</p>
        <h1>{{ activeExerciseDefinition.name }} 实时检测</h1>
        <p class="subtle">{{ activeExerciseDefinition.description }}</p>
      </div>
      <div class="header-actions">
        <select v-model="store.currentExercise" class="exercise-select" @change="onExerciseChange">
          <option v-for="exercise in exerciseOptions" :key="exercise.key" :value="exercise.key">
            {{ exercise.name }}
          </option>
        </select>
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
        <MetricTile label="当前动作" :value="activeExerciseDefinition.name" :hint="activeExerciseDefinition.key" />
        <MetricTile label="阶段" :value="store.stage" hint="当前动作阶段" />
        <MetricTile label="评分" :value="store.score" hint="实时评分" />

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
              {{ template.name }} · {{ template.view }} · {{ template.version }}
            </option>
          </select>
          <small v-if="selectedTemplate">
            {{ selectedTemplate.valid_frames || "默认" }} 帧参考曲线
          </small>
        </div>

        <div class="live-data-panel">
          <div class="live-data-header">
            <strong>实时角度</strong>
            <span>{{ currentMetrics ? "更新中" : "等待帧数据" }} · {{ activeMetricDescriptors.length }} 项</span>
          </div>
          <div class="angle-grid">
            <div v-for="metric in activeMetricDescriptors" :key="metric.key">
              <span>{{ metric.label }}</span>
              <strong>{{ formatMetricValue(currentMetrics?.[metric.key], metric.key) }}</strong>
            </div>
          </div>
        </div>

        <div class="live-data-panel">
          <div class="live-data-header">
            <strong>模板相似度</strong>
            <span>{{ displayTemplateScore?.is_partial ? "动态参考" : "完整评分" }}</span>
          </div>
          <div class="live-score-row">
            <span>动态总分</span>
            <strong>{{ formatScore(displayTemplateScore?.score) }}</strong>
          </div>
          <div class="angle-diff-list">
            <div v-for="metric in activeMetricDescriptors" :key="metric.key">
              <span>{{ metric.label }}</span>
              <b>{{ formatMetricValue(currentMetrics?.[metric.key], metric.key) }}</b>
              <b>{{ formatMetricValue(displayTemplateScore?.differences?.[metric.key], metric.key) }}</b>
              <b>{{ formatScore(displayTemplateScore?.detail_scores?.[metric.key]) }}</b>
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
        <div class="error-stack error-stack--errors">
          <strong>错误提示</strong>
          <span v-if="store.errors.length === 0" class="stack-empty">暂无错误</span>
          <span v-for="error in store.errors" :key="error">{{ error }}</span>
        </div>

        <div class="error-stack error-stack--advice">
          <strong>实时建议</strong>
          <span v-if="store.feedbacks.length === 0" class="stack-empty">暂无建议</span>
          <span v-for="advice in store.feedbacks" :key="advice">{{ advice }}</span>
        </div>

        <div class="live-data-panel ai-advice-panel">
          <div class="ai-advice-header">
            <div class="ai-advice-title">
              <span class="ai-advice-icon"><Sparkles :size="16" /></span>
              <div>
                <strong>AI 智能建议</strong>
                <small>训练结束后自动生成</small>
              </div>
            </div>
            <label class="voice-toggle-pill" :class="{ active: voiceEnabled }">
              <Volume2 :size="13" />
              <input v-model="voiceEnabled" type="checkbox" class="sr-only" />
              <span>播报</span>
            </label>
          </div>

          <div v-if="aiLoading" class="ai-advice-loading">
            <div class="ai-advice-spinner" aria-hidden="true"></div>
            <span>正在生成建议...</span>
          </div>

          <div class="ai-advice-body" :class="{ 'is-loading': aiLoading }">
            <AiAdviceContent
              theme="dark"
              :content="aiAdvice"
              :placeholder="aiLoading ? '正在生成 AI 建议，请稍候...' : 'AI 建议将在训练结束后自动生成。'"
            />
          </div>
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
            <div v-for="metric in activeMetricDescriptors" :key="metric.key" class="detail-item">
              <span class="detail-label">{{ metric.label }}</span>
              <span class="detail-value">{{ formatScore(templateScore.detail_scores?.[metric.key]) }}</span>
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
      <button class="primary-button danger" type="button" :disabled="!canSave" @click="finishTraining">
        <Square :size="18" />
        结束训练
      </button>
      <button v-if="lastSessionId && trainingState === 'finished'" class="secondary-button" type="button" @click="viewFeedback">
        <FileSearch :size="18" />
        查看本次反馈
      </button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { Camera, FileSearch, Pause, Play, RefreshCcw, Sparkles, Square, UploadCloud, Volume2 } from "lucide-vue-next";

import { apiGet, apiUpload, apiWebSocketUrl, apiPost } from "../api/client";
import { getSimpleExercises, type ExerciseLibItem } from "../api/exercises";
import { createSession, getSessions, type SessionRecord } from "../api/sessions";
import { useAuthStore } from "@/stores/auth";
import AiAdviceContent from "../components/AiAdviceContent.vue";
import MetricTile from "../components/MetricTile.vue";
import SkeletonCanvas from "../components/SkeletonCanvas.vue";
import { useAiAdvice } from "../composables/useAiAdvice";
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

type MetricValues = Record<string, number>;

type ExerciseOption = ExerciseLibItem & {
  core_angles: string[];
  core_feature_keys: string[];
};

type TemplateScore = {
  action?: string;
  template_id?: string;
  is_partial?: boolean;
  score: number;
  level: string;
  detail_scores: MetricValues;
  differences: MetricValues;
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
  frame_index?: number;
  stage?: string;
  phase?: string;
  count: number;
  valid_count: number;
  score: number;
  errors?: string[];
  issues?: string[];
  feedback?: string[];
  keypoints?: BackendKeypoints;
  metrics?: MetricValues;
  features?: MetricValues;
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
const FINISH_TIMEOUT_MS = 5000;

const router = useRouter();
const store = useTrainingStore();
const { aiAdvice, aiLoading, voiceEnabled, requestAiAdvice, clearAdvice } = useAiAdvice();
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
const currentMetrics = ref<MetricValues | null>(null);
const liveTemplateScore = ref<TemplateScore | null>(null);
const templateScore = ref<TemplateScore | null>(null);
const templateOptions = ref<TemplateOption[]>([]);
const exerciseOptions = ref<ExerciseOption[]>([]);
const selectedTemplateId = ref("");
const lastDynamicScoreAt = ref(0);
const dynamicScoreInFlight = ref(false);
const finishPending = ref(false);
const finishStatusText = ref("");
const trainingStartedAt = ref<number | null>(null);
const autoAiTriggered = ref(false);

let socket: WebSocket | null = null;
let poseLandmarker: PoseLandmarkerInstance | null = null;
let animationFrameId: number | null = null;
let videoTestTimer: ReturnType<typeof setInterval> | null = null;
let finishTimeoutId: ReturnType<typeof setTimeout> | null = null;
let videoTestUrl = "";
let lastSentAt = 0;
let motionFrames: MetricValues[] = [];
let finishRecoveryInFlight = false;

const DEFAULT_EXERCISE_OPTIONS: ExerciseOption[] = [
  {
    key: "squat",
    name: "深蹲",
    description: "评估下蹲深度、膝髋协同、躯干控制和左右稳定性。",
    supported_metrics: ["count", "valid_count", "score", "depth_ratio"],
    core_angles: ["膝角", "髋角", "躯干倾斜角", "左右膝差"],
    core_feature_keys: ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"],
  },
  {
    key: "push_up",
    name: "俯卧撑",
    description: "评估肘部屈伸幅度、肩部控制、身体直线和髋部稳定。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["肘角", "肩角", "身体直线角", "髋部塌陷角"],
    core_feature_keys: ["elbow_angle", "shoulder_angle", "body_line_angle", "hip_sag_angle"],
  },
  {
    key: "plank",
    name: "平板支撑",
    description: "评估肩髋踝连线、髋部姿态、颈部角度和保持稳定性。",
    supported_metrics: ["duration", "score", "error_count"],
    core_angles: ["肩髋踝直线角", "髋部角", "颈部角"],
    core_feature_keys: ["body_line_angle", "hip_angle", "neck_angle"],
  },
  {
    key: "jumping_jack",
    name: "开合跳",
    description: "评估肩外展、双腿打开幅度、手腕高度和脚踝间距。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["肩外展角", "双腿夹角", "手腕高度", "脚踝距离"],
    core_feature_keys: ["shoulder_abduction_angle", "leg_spread_angle", "wrist_height", "ankle_distance"],
  },
  {
    key: "lunge",
    name: "弓步蹲",
    description: "评估膝关节角度、髋部控制和躯干稳定性。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["膝角", "髋角", "躯干倾斜角", "左右膝差"],
    core_feature_keys: ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"],
  },
  {
    key: "glute_bridge",
    name: "臀桥",
    description: "评估髋部伸展幅度和身体直线。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["髋角", "身体直线角"],
    core_feature_keys: ["hip_angle", "body_line_angle"],
  },
  {
    key: "high_knees",
    name: "高抬腿",
    description: "评估抬膝高度和节奏。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["抬膝高度", "膝角"],
    core_feature_keys: ["knee_height", "knee_angle"],
  },
  {
    key: "burpee",
    name: "波比跳",
    description: "评估髋肩角度和身体控制。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["髋角", "身体直线角", "手腕高度"],
    core_feature_keys: ["hip_angle", "body_line_angle", "wrist_height"],
  },
  {
    key: "mountain_climber",
    name: "登山跑",
    description: "评估平板姿势、提膝高度和核心稳定。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["身体直线角", "髋角", "提膝高度"],
    core_feature_keys: ["body_line_angle", "hip_angle", "knee_raise"],
  },
  {
    key: "pull_up",
    name: "引体向上",
    description: "评估上拉幅度、身体控制和左右对称。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["肘角", "身体摆动", "左右对称差"],
    core_feature_keys: ["elbow_angle", "body_line_angle", "symmetry_diff"],
  },
  {
    key: "dumbbell_curl",
    name: "哑铃弯举",
    description: "评估弯举幅度和上臂稳定性。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["肘角", "肩角", "左右对称差"],
    core_feature_keys: ["elbow_angle", "shoulder_angle", "symmetry_diff"],
  },
  {
    key: "dumbbell_press",
    name: "哑铃推举",
    description: "评估推举幅度和肩部控制。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["肘角", "肩角", "左右对称差"],
    core_feature_keys: ["elbow_angle", "shoulder_angle", "symmetry_diff"],
  },
  {
    key: "russian_twist",
    name: "俄罗斯转体",
    description: "评估躯干旋转幅度和核心控制。",
    supported_metrics: ["count", "valid_count", "score"],
    core_angles: ["旋转幅度", "躯干角"],
    core_feature_keys: ["rotation_offset", "trunk_angle"],
  },
];

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
const canSave = computed(() => (trainingState.value === "running" || trainingState.value === "paused") && !finishPending.value);
const hasAdviceData = computed(() => {
  const templateErrors = templateScore.value?.errors ?? [];
  const templateSuggestions = templateScore.value?.suggestions ?? [];
  return (
    store.errors.length > 0
    || store.feedbacks.length > 0
    || store.count > 0
    || templateErrors.length > 0
    || templateSuggestions.length > 0
  );
});
const displayTemplateScore = computed(() => liveTemplateScore.value ?? templateScore.value);
const selectedTemplate = computed(() =>
  templateOptions.value.find((template) => template.template_id === selectedTemplateId.value)
);
const activeExerciseDefinition = computed<ExerciseOption>(() =>
  exerciseOptions.value.find((exercise) => exercise.key === store.currentExercise)
  ?? DEFAULT_EXERCISE_OPTIONS.find((exercise) => exercise.key === store.currentExercise)
  ?? DEFAULT_EXERCISE_OPTIONS[0]
);
const activeMetricDescriptors = computed(() =>
  activeExerciseDefinition.value.core_feature_keys.map((key, index) => ({
    key,
    label: activeExerciseDefinition.value.core_angles[index] ?? key,
  }))
);

async function generateAiAdvice() {
  if (!hasAdviceData.value) return;

  const errors = [
    ...store.errors,
    ...(templateScore.value?.errors ?? []),
  ].filter(Boolean);
  const feedbacks = [
    ...store.feedbacks,
    ...(templateScore.value?.suggestions ?? []),
  ].filter(Boolean);

  await requestAiAdvice({
    exercise: store.currentExercise,
    stage: store.stage,
    errors: [...new Set(errors)],
    feedbacks: [...new Set(feedbacks)],
  });
}

function scheduleAutoAiAdvice() {
  if (autoAiTriggered.value || aiLoading.value || !hasAdviceData.value) return;
  autoAiTriggered.value = true;
  window.setTimeout(() => {
    void generateAiAdvice();
  }, 800);
}

watch(trainingState, (state) => {
  if (state === "finished") {
    scheduleAutoAiAdvice();
  }
});

function formatAngle(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(1)}°` : "--";
}

function formatDistance(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(3) : "--";
}

function formatScore(value?: number) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "--";
}

function formatMetricValue(value: number | undefined, key: string) {
  return key.includes("height") || key.includes("distance") ? formatDistance(value) : formatAngle(value);
}

function normalizeExerciseOptions(items: ExerciseLibItem[]) {
  return items.map((item) => ({
    ...item,
    core_angles: item.core_angles ?? [],
    core_feature_keys: item.core_feature_keys ?? [],
  }));
}

async function loadExerciseOptions() {
  try {
    const response = await getSimpleExercises();
    const items = normalizeExerciseOptions(response.items || []);
    exerciseOptions.value = items.length > 0 ? items : DEFAULT_EXERCISE_OPTIONS;
  } catch (error) {
    console.error("加载动作定义失败:", error);
    exerciseOptions.value = DEFAULT_EXERCISE_OPTIONS;
  }
}

async function loadTemplateOptions() {
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

function onExerciseChange() {
  store.setExercise(store.currentExercise);
  resetTraining();
  loadTemplateOptions();
  // Update WebSocket with new exercise type
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "start", exercise_type: store.currentExercise }));
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
  autoAiTriggered.value = false;
  clearAdvice();
  poseStatus.value = "";
  cameraError.value = "";
  store.resetLiveMetrics();
  resetDynamicTemplateState(true);
  resetFinishState();
  trainingStartedAt.value = null;
  clearPoseCanvas(overlayRef.value);
  stopVideoTestPlayback();

  if (!cameraActive.value || !poseLandmarker) {
    await connectCamera();
  } else {
    await openRealtimeSocket();
  }

  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  trainingState.value = "connecting";
  socket.send(JSON.stringify({ type: "start", exercise_type: store.currentExercise }));
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
  autoAiTriggered.value = false;
  clearAdvice();
  poseStatus.value = "";
  cameraError.value = "";
  store.resetLiveMetrics();
  resetDynamicTemplateState(true);
  resetFinishState();
  trainingStartedAt.value = null;
  clearPoseCanvas(overlayRef.value);

  if (socket?.readyState === WebSocket.OPEN) {
    trainingState.value = "connecting";
    socket.send(JSON.stringify({ type: "start", exercise_type: store.currentExercise }));
  } else {
    trainingState.value = "idle";
  }
}

async function finishTraining() {
  if (finishPending.value) return;

  savedMessage.value = "";
  cameraError.value = "";
  finishPending.value = true;
  finishStatusText.value = "正在保存本次训练结果，请稍候...";

  stopPoseLoop();
  stopVideoTestPlayback();

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    await saveSessionFallback("实时通道已断开，已根据当前统计补存本次训练记录。", true);
    return;
  }

  clearFinishTimeout();
  finishTimeoutId = setTimeout(() => {
    void recoverAndRouteAfterFinish("结束训练响应超时，已尝试恢复本次训练记录。");
  }, FINISH_TIMEOUT_MS);

  socket.send(JSON.stringify({ type: "finish" }));
}

function viewFeedback() {
  if (lastSessionId.value) {
    router.push({ path: "/feedback", query: { session: lastSessionId.value, from: "realtime" } });
  }
}

function openRealtimeSocket(): Promise<void> {
  if (socket?.readyState === WebSocket.OPEN) {
    return Promise.resolve();
  }

  closeSocket();
  trainingState.value = "connecting";

  return new Promise((resolve, reject) => {
    // Pass JWT token for WebSocket auth
    const authStore = useAuthStore();
    const tokenParam = authStore.token ? `?token=${encodeURIComponent(authStore.token)}` : "";
    socket = new WebSocket(apiWebSocketUrl(`/realtime/pose${tokenParam}`));

    socket.onopen = () => resolve();
    socket.onerror = () => {
      resetFinishState();
      cameraError.value = "实时检测通道连接失败，请确认后端服务已启动。";
      trainingState.value = "error";
      reject(new Error("WebSocket connection failed"));
    };
    socket.onclose = () => {
      stopPoseLoop();
      if (finishPending.value) {
        void recoverAndRouteAfterFinish("实时通道已断开，已尝试恢复本次训练记录。");
      }
      if (trainingState.value === "running" || trainingState.value === "connecting") {
        trainingState.value = "error";
      }
    };
    socket.onmessage = (event) => handleRealtimeMessage(JSON.parse(event.data));
  });
}

function handleRealtimeMessage(message: Record<string, any>) {
  console.log("收到消息:", message);

  if (message.type === "status") {
    console.log("状态消息:", message.state);
    if (message.state === "running") {
      if (!trainingStartedAt.value) {
        trainingStartedAt.value = Date.now();
      }
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
    resetFinishState();
    trainingState.value = "finished";
    stopPoseLoop();
    poseStatus.value = "";

    if (motionFrames.length > 0) {
      scoreByTemplate();
    }

    const session = message.session as { session_id?: string; total_count?: number } | undefined;
    lastSessionId.value = session?.session_id ?? "";

    if (session?.session_id) {
      savedMessage.value = "训练已结束，正在跳转到本次反馈。";
      void router.push({ path: "/feedback", query: { session: session.session_id, from: "realtime" } });
    } else {
      void recoverAndRouteAfterFinish("训练已结束，已恢复本次训练记录并准备跳转反馈页。");
    }
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
  drawPose(canvas, landmarks, video, "cover");

  if (!landmarks) {
    poseStatus.value = "未检测到人体，请站入画面";
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
  poseStatus.value = "正在加载姿态识别模型..";
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

    socket.send(JSON.stringify({ type: "start", exercise_type: store.currentExercise }));
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

function clearFinishTimeout() {
  if (finishTimeoutId) {
    clearTimeout(finishTimeoutId);
    finishTimeoutId = null;
  }
}

function resetFinishState() {
  clearFinishTimeout();
  finishPending.value = false;
  finishStatusText.value = "";
}

function buildFallbackSessionPayload() {
  const durationSeconds = trainingStartedAt.value
    ? Math.max(1, Math.round((Date.now() - trainingStartedAt.value) / 1000))
    : 0;
  const totalCount = Number(store.count ?? 0);
  const validCount = Number(store.validCount ?? 0);
  const averageScore = Number(store.score ?? 0);

  return {
    exercise: store.currentExercise,
    duration_seconds: durationSeconds,
    total_count: totalCount,
    valid_count: validCount,
    error_count: Math.max(0, totalCount - validCount),
    average_score: averageScore,
  };
}

function isRecentMatchingSession(session: SessionRecord, payload: ReturnType<typeof buildFallbackSessionPayload>) {
  const createdAt = Date.parse(session.created_at);
  const recentEnough = Number.isFinite(createdAt) && Math.abs(Date.now() - createdAt) <= 2 * 60 * 1000;
  return recentEnough
    && session.exercise === payload.exercise
    && session.total_count === payload.total_count
    && session.valid_count === payload.valid_count
    && session.error_count === payload.error_count;
}

async function recoverLatestSession(payload: ReturnType<typeof buildFallbackSessionPayload>) {
  try {
    const response = await getSessions({ limit: 10, exercise: payload.exercise });
    return response.items.find((item) => isRecentMatchingSession(item, payload)) ?? null;
  } catch (error) {
    console.error("查询最近训练记录失败:", error);
    return null;
  }
}

async function recoverAndRouteAfterFinish(successMessage: string) {
  if (finishRecoveryInFlight) return;
  finishRecoveryInFlight = true;
  finishStatusText.value = "正在恢复本次训练记录...";

  try {
    const payload = buildFallbackSessionPayload();
    const existingSession = payload.total_count > 0
      ? await recoverLatestSession(payload)
      : null;
    if (existingSession?.session_id) {
      lastSessionId.value = existingSession.session_id;
      resetFinishState();
      trainingState.value = "finished";
      savedMessage.value = successMessage;
      await router.push({ path: "/feedback", query: { session: existingSession.session_id, from: "realtime" } });
      return;
    }

    await saveSessionFallback(successMessage, true);
  } finally {
    finishRecoveryInFlight = false;
  }
}

async function saveSessionFallback(successMessage: string, allowZeroCount = false) {
  const payload = buildFallbackSessionPayload();

  if (payload.total_count <= 0 && !allowZeroCount) {
    resetFinishState();
    trainingState.value = "finished";
    savedMessage.value = "本次没有完成动作，未生成训练记录。";
    return;
  }

  try {
    finishStatusText.value = "实时通道异常，正在用当前统计补存训练记录...";
    const session = await createSession({
      ...payload,
      issues: [...new Set(store.errors.filter(Boolean))],
      suggestions: [...new Set(store.feedbacks.filter(Boolean))],
    });
    lastSessionId.value = session.session_id;
    resetFinishState();
    trainingState.value = "finished";
    savedMessage.value = successMessage;
    await router.push({ path: "/feedback", query: { session: session.session_id, from: "realtime" } });
  } catch (error) {
    console.error("训练记录补存失败:", error);
    resetFinishState();
    trainingState.value = "error";
    cameraError.value = "结束训练失败，实时通道已断开且补存训练记录未成功。请重新开始检测。";
  }
}

function playVideoTestResult(result: VideoTestResponse) {
  if (result.frames.length === 0) {
    poseStatus.value = "视频没有产生可用的实时检测帧";
    trainingState.value = "finished";
    return;
  }

  let frameIndex = 0;
  trainingState.value = "running";
  poseStatus.value = "正在按实时节奏播放视频检测结果..";
  if (!trainingStartedAt.value) {
    trainingStartedAt.value = Date.now();
  }

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

  const sourceMetrics = frame.metrics ?? frame.features;
  if (!sourceMetrics) return;

  const metrics: MetricValues = {};
  for (const { key } of activeMetricDescriptors.value) {
    const rawValue = sourceMetrics[key];
    if (typeof rawValue === "number" && Number.isFinite(rawValue)) {
      metrics[key] = Number(rawValue);
    }
  }

  if (Object.keys(metrics).length === 0) return;

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
  if (motionFrames.length < 2) return;

  if (mode === "live") {
    dynamicScoreInFlight.value = true;
  }

  try {
    const response = await apiPost<TemplateScore>("/realtime/score-action", {
      action: store.currentExercise,
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
    stage: String(frame.stage ?? frame.phase ?? "ready"),
    count: Number(frame.count ?? 0),
    valid_count: Number(frame.valid_count ?? 0),
    score: Number(frame.score ?? 0),
    errors: Array.isArray(frame.errors)
      ? frame.errors
      : Array.isArray(frame.issues)
        ? frame.issues
        : [],
    feedback: Array.isArray(frame.feedback) ? frame.feedback : [],
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
  clearFinishTimeout();
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

onMounted(async () => {
  await loadExerciseOptions();
  await loadTemplateOptions();
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

<style scoped>
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

.primary-button.danger {
  background: var(--danger, #c84a3a);
}

.primary-button.danger:hover {
  background: #b33d2e;
}

.primary-button.danger:disabled {
  background: var(--danger, #c84a3a);
  opacity: 0.58;
}

.ai-advice-panel {
  gap: 14px;
  background: rgba(2, 6, 23, 0.38);
  border-color: #253047;
}

.ai-advice-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.ai-advice-title {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.ai-advice-title strong {
  display: block;
  color: #f8fafc;
  font-size: 14px;
}

.ai-advice-title small {
  display: block;
  margin-top: 2px;
  color: #94a3b8;
  font-size: 11px;
  font-weight: 400;
}

.ai-advice-icon {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
}

.voice-toggle-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 6px 10px;
  border: 1px solid #334155;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.72);
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.voice-toggle-pill.active {
  border-color: #6366f1;
  background: rgba(79, 70, 229, 0.22);
  color: #c7d2fe;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.ai-advice-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: #cbd5e1;
  font-size: 12px;
}

.ai-advice-spinner {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border: 2px solid rgba(148, 163, 184, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: ai-advice-spin 0.8s linear infinite;
}

.ai-advice-body {
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(2, 6, 23, 0.42);
  border: 1px solid #253047;
}

.ai-advice-body.is-loading {
  opacity: 0.55;
}

@keyframes ai-advice-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
