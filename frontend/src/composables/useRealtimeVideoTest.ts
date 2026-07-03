import { onBeforeUnmount, ref, type Ref } from "vue";
import { useRouter } from "vue-router";

import { apiWebSocketUrl } from "../api/client";
import { createSession, getSessions, type SessionRecord } from "../api/sessions";
import {
  clearPoseCanvas,
  createPoseLandmarker,
  detectPose,
  drawPose,
  toBackendKeypoints,
} from "../services/poseLandmarker";
import { useAuthStore } from "../stores/auth";
import { useTrainingStore } from "../stores/training";

type TrainingState = "idle" | "connecting" | "running" | "paused" | "finished" | "error";
type PoseLandmarkerInstance = Awaited<ReturnType<typeof createPoseLandmarker>>;

type VideoTestFrame = {
  stage: string;
  count: number;
  valid_count: number;
  score: number;
  errors: string[];
  feedback?: string[];
};

const SEND_INTERVAL_MS = 100;
const FINISH_TIMEOUT_MS = 5000;

export function useRealtimeVideoTest(options: {
  exercise: Ref<string>;
  videoRef: Ref<HTMLVideoElement | null>;
  overlayRef: Ref<HTMLCanvasElement | null>;
}) {
  const router = useRouter();
  const store = useTrainingStore();

  const trainingState = ref<TrainingState>("idle");
  const poseStatus = ref("");
  const cameraError = ref("");
  const message = ref("");
  const analyzing = ref(false);
  const finishPending = ref(false);
  const finishStatusText = ref("");

  let socket: WebSocket | null = null;
  let poseLandmarker: PoseLandmarkerInstance | null = null;
  let animationFrameId: number | null = null;
  let finishTimeoutId: ReturnType<typeof setTimeout> | null = null;
  let videoTestUrl = "";
  let lastSentAt = 0;
  let trainingStartedAt: number | null = null;
  let finishRecoveryInFlight = false;

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

  function stopPoseLoop() {
    if (animationFrameId !== null) {
      window.cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
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

  function buildFallbackSessionPayload() {
    const durationSeconds = trainingStartedAt
      ? Math.max(1, Math.round((Date.now() - trainingStartedAt) / 1000))
      : 0;
    const totalCount = Number(store.count ?? 0);
    const validCount = Number(store.validCount ?? 0);

    return {
      exercise: options.exercise.value,
      duration_seconds: durationSeconds,
      total_count: totalCount,
      valid_count: validCount,
      error_count: Math.max(0, totalCount - validCount),
      average_score: Number(store.score ?? 0),
    };
  }

  function isRecentMatchingSession(
    session: SessionRecord,
    payload: ReturnType<typeof buildFallbackSessionPayload>,
  ) {
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

  async function routeToFeedback(sessionId: string, successMessage: string) {
    message.value = successMessage;
    await router.push({
      path: "/feedback",
      query: { session: sessionId, from: "realtime" },
    });
  }

  async function saveSessionFallback(successMessage: string) {
    const payload = buildFallbackSessionPayload();

    if (payload.total_count <= 0) {
      resetFinishState();
      trainingState.value = "finished";
      message.value = "本次没有完成动作，未生成训练记录。";
      return;
    }

    try {
      finishStatusText.value = "实时通道异常，正在用当前统计补存训练记录...";
      const session = await createSession({
        ...payload,
        issues: [...new Set(store.errors.filter(Boolean))],
        suggestions: [...new Set(store.feedbacks.filter(Boolean))],
      });
      resetFinishState();
      trainingState.value = "finished";
      await routeToFeedback(session.session_id, successMessage);
    } catch (error) {
      console.error("训练记录补存失败:", error);
      resetFinishState();
      trainingState.value = "error";
      cameraError.value = "分析结束失败，请重新开始。";
    }
  }

  async function recoverAndRouteAfterFinish(successMessage: string) {
    if (finishRecoveryInFlight) return;
    finishRecoveryInFlight = true;
    finishStatusText.value = "正在恢复本次训练记录...";

    try {
      const payload = buildFallbackSessionPayload();
      if (payload.total_count <= 0) {
        resetFinishState();
        trainingState.value = "finished";
        message.value = "本次没有完成动作，未生成训练记录。";
        return;
      }

      const existingSession = await recoverLatestSession(payload);
      if (existingSession?.session_id) {
        resetFinishState();
        trainingState.value = "finished";
        await routeToFeedback(existingSession.session_id, successMessage);
        return;
      }

      await saveSessionFallback(successMessage);
    } finally {
      finishRecoveryInFlight = false;
    }
  }

  async function finishTraining() {
    if (finishPending.value) return;

    cameraError.value = "";
    finishPending.value = true;
    finishStatusText.value = "正在保存分析结果，请稍候...";
    stopPoseLoop();

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      await saveSessionFallback("分析已完成，已根据当前统计补存训练记录。");
      return;
    }

    clearFinishTimeout();
    finishTimeoutId = setTimeout(() => {
      void recoverAndRouteAfterFinish("结束分析响应超时，已尝试恢复训练记录。");
    }, FINISH_TIMEOUT_MS);

    socket.send(JSON.stringify({ type: "finish" }));
  }

  function handleAnalysisFrame(frame: VideoTestFrame) {
    store.updateLiveMetrics({
      stage: String(frame.stage),
      count: Number(frame.count ?? 0),
      valid_count: Number(frame.valid_count ?? 0),
      score: Number(frame.score ?? 0),
      errors: Array.isArray(frame.errors) ? frame.errors : [],
      feedback: Array.isArray(frame.feedback) ? frame.feedback : [],
    });
  }

  function handleRealtimeMessage(messageData: Record<string, unknown>) {
    if (messageData.type === "status") {
      if (messageData.state === "running") {
        if (!trainingStartedAt) {
          trainingStartedAt = Date.now();
        }
        trainingState.value = "running";
        poseStatus.value = "正在分析视频...";
        startPoseLoop();
      }
      return;
    }

    if (messageData.type === "analysis") {
      handleAnalysisFrame(messageData as VideoTestFrame);
      return;
    }

    if (messageData.type === "summary") {
      resetFinishState();
      trainingState.value = "finished";
      stopPoseLoop();
      poseStatus.value = "";
      analyzing.value = false;

      const session = messageData.session as { session_id?: string } | undefined;
      if (session?.session_id) {
        void routeToFeedback(session.session_id, "分析完成，正在跳转到反馈页。");
      } else {
        void recoverAndRouteAfterFinish("分析完成，正在恢复训练记录并跳转反馈页。");
      }
    }
  }

  function openRealtimeSocket(): Promise<void> {
    if (socket?.readyState === WebSocket.OPEN) {
      return Promise.resolve();
    }

    closeSocket();
    trainingState.value = "connecting";

    return new Promise((resolve, reject) => {
      const authStore = useAuthStore();
      const tokenParam = authStore.token ? `?token=${encodeURIComponent(authStore.token)}` : "";
      socket = new WebSocket(apiWebSocketUrl(`/realtime/pose${tokenParam}`));

      socket.onopen = () => resolve();
      socket.onerror = () => {
        resetFinishState();
        cameraError.value = "实时分析通道连接失败，请确认后端服务已启动。";
        trainingState.value = "error";
        analyzing.value = false;
        reject(new Error("WebSocket connection failed"));
      };
      socket.onclose = () => {
        stopPoseLoop();
        if (finishPending.value) {
          void recoverAndRouteAfterFinish("分析通道已断开，正在尝试恢复训练记录。");
        }
        if (trainingState.value === "running" || trainingState.value === "connecting") {
          trainingState.value = "error";
          analyzing.value = false;
        }
      };
      socket.onmessage = (event) => handleRealtimeMessage(JSON.parse(event.data));
    });
  }

  function startPoseLoop() {
    stopPoseLoop();
    lastSentAt = 0;
    animationFrameId = window.requestAnimationFrame(runPoseFrame);
  }

  function runPoseFrame(timestamp: number) {
    if (trainingState.value !== "running") return;

    const video = options.videoRef.value;
    const canvas = options.overlayRef.value;

    if (!video || !canvas || !poseLandmarker || !socket || socket.readyState !== WebSocket.OPEN) {
      animationFrameId = window.requestAnimationFrame(runPoseFrame);
      return;
    }

    const landmarks = detectPose(poseLandmarker, video, timestamp);
    drawPose(canvas, landmarks, video, "contain");

    if (!landmarks) {
      poseStatus.value = "未检测到人体，请确认视频中人物清晰可见";
    } else {
      poseStatus.value = "";
      if (timestamp - lastSentAt >= SEND_INTERVAL_MS) {
        lastSentAt = timestamp;
        socket.send(JSON.stringify({
          type: "frame",
          exercise: options.exercise.value,
          timestamp: Date.now(),
          keypoints: toBackendKeypoints(landmarks),
        }));
      }
    }

    if (videoTestUrl && video.duration > 0 && video.currentTime >= video.duration) {
      void finishTraining();
      return;
    }

    animationFrameId = window.requestAnimationFrame(runPoseFrame);
  }

  function showVideoPreview(file: File) {
    revokeVideoTestUrl();
    videoTestUrl = URL.createObjectURL(file);

    const video = options.videoRef.value;
    if (video) {
      const stream = video.srcObject as MediaStream | null;
      stream?.getTracks().forEach((track) => track.stop());
      video.srcObject = null;
      video.src = videoTestUrl;
      video.loop = false;
      video.currentTime = 0;
      void video.play().catch(() => undefined);
    }
  }

  async function analyzeVideoFile(file: File) {
    closeSocket();
    clearPoseCanvas(options.overlayRef.value);
    store.resetLiveMetrics();
    store.setExercise(options.exercise.value);
    resetFinishState();
    cameraError.value = "";
    message.value = "";
    poseStatus.value = "正在加载姿态识别模型...";
    analyzing.value = true;
    trainingState.value = "connecting";
    trainingStartedAt = null;

    try {
      if (!poseLandmarker) {
        poseLandmarker = await createPoseLandmarker();
      }

      await openRealtimeSocket();
      if (!socket || socket.readyState !== WebSocket.OPEN) {
        throw new Error("无法连接到实时分析通道");
      }

      showVideoPreview(file);
      socket.send(JSON.stringify({ type: "start", exercise_type: options.exercise.value }));
      message.value = `正在分析：${file.name}`;
    } catch (error) {
      console.error("视频分析失败:", error);
      cameraError.value = "视频分析失败，请确认后端服务已启动且视频格式可读。";
      poseStatus.value = "";
      trainingState.value = "error";
      analyzing.value = false;
    }
  }

  function cleanup() {
    closeSocket();
    clearPoseCanvas(options.overlayRef.value);
    revokeVideoTestUrl();
  }

  onBeforeUnmount(cleanup);

  return {
    trainingState,
    poseStatus,
    cameraError,
    message,
    analyzing,
    finishPending,
    finishStatusText,
    analyzeVideoFile,
    cleanup,
  };
}
