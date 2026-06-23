import {
  FilesetResolver,
  PoseLandmarker,
  type NormalizedLandmark,
} from "@mediapipe/tasks-vision";

export type BackendKeypoint = {
  x: number;
  y: number;
  visibility: number;
};

export type BackendKeypoints = Record<string, BackendKeypoint>;

const BASE_URL = import.meta.env.BASE_URL ?? "/";
const ASSET_BASE = BASE_URL.endsWith("/") ? BASE_URL : `${BASE_URL}/`;
const WASM_PATH = `${ASSET_BASE}mediapipe/wasm`;
const MODEL_PATH = `${ASSET_BASE}mediapipe/models/pose_landmarker_lite.task`;

const LANDMARK_NAMES: Record<number, string> = {
  0: "nose",
  1: "left_eye_inner",
  2: "left_eye",
  3: "left_eye_outer",
  4: "right_eye_inner",
  5: "right_eye",
  6: "right_eye_outer",
  7: "left_ear",
  8: "right_ear",
  9: "mouth_left",
  10: "mouth_right",
  11: "left_shoulder",
  12: "right_shoulder",
  13: "left_elbow",
  14: "right_elbow",
  15: "left_wrist",
  16: "right_wrist",
  17: "left_pinky",
  18: "right_pinky",
  19: "left_index",
  20: "right_index",
  21: "left_thumb",
  22: "right_thumb",
  23: "left_hip",
  24: "right_hip",
  25: "left_knee",
  26: "right_knee",
  27: "left_ankle",
  28: "right_ankle",
  29: "left_heel",
  30: "right_heel",
  31: "left_foot_index",
  32: "right_foot_index",
};

const BODY_CONNECTIONS: Array<[number, number]> = [
  [11, 12],
  [11, 13],
  [13, 15],
  [12, 14],
  [14, 16],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25],
  [25, 27],
  [24, 26],
  [26, 28],
  [27, 29],
  [29, 31],
  [28, 30],
  [30, 32],
];

let poseLandmarkerPromise: Promise<PoseLandmarker> | null = null;

export function createPoseLandmarker() {
  if (!poseLandmarkerPromise) {
    poseLandmarkerPromise = FilesetResolver.forVisionTasks(WASM_PATH).then(async (vision) => {
      try {
        return await createLandmarkerWithDelegate(vision, "GPU");
      } catch {
        return createLandmarkerWithDelegate(vision, "CPU");
      }
    });
  }

  return poseLandmarkerPromise;
}

function createLandmarkerWithDelegate(
  vision: Awaited<ReturnType<typeof FilesetResolver.forVisionTasks>>,
  delegate: "CPU" | "GPU",
) {
  return PoseLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: MODEL_PATH,
      delegate,
    },
    runningMode: "VIDEO",
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
  });
}

export function detectPose(
  landmarker: PoseLandmarker,
  video: HTMLVideoElement,
  timestampMs: number,
): NormalizedLandmark[] | null {
  if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
    return null;
  }

  const result = landmarker.detectForVideo(video, timestampMs);
  return result.landmarks[0] ?? null;
}

export function toBackendKeypoints(landmarks: NormalizedLandmark[]): BackendKeypoints {
  const keypoints: BackendKeypoints = {};

  for (const [indexText, name] of Object.entries(LANDMARK_NAMES)) {
    const landmark = landmarks[Number(indexText)];
    if (!landmark) continue;

    keypoints[name] = {
      x: roundPoint(landmark.x),
      y: roundPoint(landmark.y),
      visibility: roundPoint(landmark.visibility ?? 1),
    };
  }

  return keypoints;
}

export function drawPose(canvas: HTMLCanvasElement, landmarks: NormalizedLandmark[] | null) {
  const context = canvas.getContext("2d");
  if (!context) return;

  syncCanvasSize(canvas);
  context.clearRect(0, 0, canvas.width, canvas.height);

  if (!landmarks) {
    drawPoseMessage(canvas, context, "未检测到人体，请站入画面");
    return;
  }

  context.lineCap = "round";
  context.lineJoin = "round";

  for (const [from, to] of BODY_CONNECTIONS) {
    const start = landmarks[from];
    const end = landmarks[to];
    if (!isVisible(start) || !isVisible(end)) continue;

    context.beginPath();
    context.moveTo(start.x * canvas.width, start.y * canvas.height);
    context.lineTo(end.x * canvas.width, end.y * canvas.height);
    context.strokeStyle = "rgba(240, 178, 63, 0.96)";
    context.lineWidth = 5;
    context.shadowColor = "rgba(16, 23, 19, 0.7)";
    context.shadowBlur = 8;
    context.stroke();
  }

  context.shadowBlur = 0;
  for (const landmark of landmarks) {
    if (!isVisible(landmark)) continue;

    const x = landmark.x * canvas.width;
    const y = landmark.y * canvas.height;
    context.beginPath();
    context.arc(x, y, 5, 0, Math.PI * 2);
    context.fillStyle = "rgba(215, 239, 227, 0.96)";
    context.fill();
    context.lineWidth = 2;
    context.strokeStyle = "rgba(18, 28, 23, 0.86)";
    context.stroke();
  }
}

export function clearPoseCanvas(canvas: HTMLCanvasElement | null) {
  const context = canvas?.getContext("2d");
  if (!canvas || !context) return;
  context.clearRect(0, 0, canvas.width, canvas.height);
}

function syncCanvasSize(canvas: HTMLCanvasElement) {
  const width = Math.max(1, Math.floor(canvas.clientWidth));
  const height = Math.max(1, Math.floor(canvas.clientHeight));

  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
}

function drawPoseMessage(
  canvas: HTMLCanvasElement,
  context: CanvasRenderingContext2D,
  message: string,
) {
  context.fillStyle = "rgba(18, 28, 23, 0.72)";
  context.fillRect(18, canvas.height - 70, Math.min(320, canvas.width - 36), 46);
  context.fillStyle = "#fff7df";
  context.font = "700 14px Microsoft YaHei, PingFang SC, sans-serif";
  context.fillText(message, 34, canvas.height - 42);
}

function isVisible(landmark?: NormalizedLandmark) {
  return Boolean(landmark && (landmark.visibility ?? 1) >= 0.45);
}

function roundPoint(value: number) {
  return Math.round(value * 10000) / 10000;
}
