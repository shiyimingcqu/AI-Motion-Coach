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

export type PoseReplayLandmark = {
  x: number;
  y: number;
  z: number;
  visibility: number;
};

const NAME_TO_INDEX: Record<string, number> = {
  nose: 0,
  left_eye_inner: 1,
  left_eye: 2,
  left_eye_outer: 3,
  right_eye_inner: 4,
  right_eye: 5,
  right_eye_outer: 6,
  left_ear: 7,
  right_ear: 8,
  mouth_left: 9,
  mouth_right: 10,
  left_shoulder: 11,
  right_shoulder: 12,
  left_elbow: 13,
  right_elbow: 14,
  left_wrist: 15,
  right_wrist: 16,
  left_pinky: 17,
  right_pinky: 18,
  left_index: 19,
  right_index: 20,
  left_thumb: 21,
  right_thumb: 22,
  left_hip: 23,
  right_hip: 24,
  left_knee: 25,
  right_knee: 26,
  left_ankle: 27,
  right_ankle: 28,
  left_heel: 29,
  right_heel: 30,
  left_foot_index: 31,
  right_foot_index: 32,
};

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
  [0, 1], [1, 2], [2, 3], [3, 7],
  [0, 4], [4, 5], [5, 6], [6, 8],
  [9, 10],
  [11, 12],
  [11, 13], [13, 15], [15, 17], [15, 19], [15, 21], [17, 19],
  [12, 14], [14, 16], [16, 18], [16, 20], [16, 22], [18, 20],
  [11, 23],
  [12, 24],
  [23, 24],
  [23, 25], [25, 27], [27, 29], [29, 31],
  [24, 26], [26, 28], [28, 30], [30, 32],
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

export function toReplayLandmarks(landmarks: NormalizedLandmark[]): PoseReplayLandmark[] {
  return landmarks.slice(0, 33).map((landmark) => ({
    x: roundPoint(landmark.x),
    y: roundPoint(landmark.y),
    z: roundPoint(landmark.z ?? 0),
    visibility: roundPoint(landmark.visibility ?? 1),
  }));
}

export function drawPose(
  canvas: HTMLCanvasElement,
  landmarks: NormalizedLandmark[] | null,
  video?: HTMLVideoElement | null,
  fit: "contain" | "cover" | "fill" = "fill",
) {
  const context = canvas.getContext("2d");
  if (!context) return;

  syncCanvasSize(canvas);
  context.clearRect(0, 0, canvas.width, canvas.height);

  if (!landmarks) {
    drawPoseMessage(canvas, context, "未检测到人体，请站入画面");
    return;
  }

  const displayRect = getVideoDisplayRect(canvas, video, fit);

  context.lineCap = "round";
  context.lineJoin = "round";

  for (const [from, to] of BODY_CONNECTIONS) {
    const start = landmarks[from];
    const end = landmarks[to];
    if (!isVisible(start) || !isVisible(end)) continue;

    const startPoint = mapLandmarkToCanvas(start, displayRect);
    const endPoint = mapLandmarkToCanvas(end, displayRect);

    context.beginPath();
    context.moveTo(startPoint.x, startPoint.y);
    context.lineTo(endPoint.x, endPoint.y);
    context.strokeStyle = "rgba(240, 178, 63, 0.96)";
    context.lineWidth = 5;
    context.shadowColor = "rgba(16, 23, 19, 0.7)";
    context.shadowBlur = 8;
    context.stroke();
  }

  context.shadowBlur = 0;
  for (const landmark of landmarks) {
    if (!isVisible(landmark)) continue;

    const { x, y } = mapLandmarkToCanvas(landmark, displayRect);
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

function getVideoDisplayRect(
  canvas: HTMLCanvasElement,
  video: HTMLVideoElement | null | undefined,
  fit: "contain" | "cover" | "fill",
) {
  const targetWidth = canvas.clientWidth || canvas.width;
  const targetHeight = canvas.clientHeight || canvas.height;

  if (!video || fit === "fill" || !video.videoWidth || !video.videoHeight) {
    return { x: 0, y: 0, width: targetWidth, height: targetHeight };
  }

  const sourceWidth = video.videoWidth;
  const sourceHeight = video.videoHeight;
  const sourceRatio = sourceWidth / sourceHeight;
  const targetRatio = targetWidth / targetHeight;

  if (fit === "contain") {
    if (sourceRatio > targetRatio) {
      const width = targetWidth;
      const height = targetWidth / sourceRatio;
      return { x: 0, y: (targetHeight - height) / 2, width, height };
    }

    const height = targetHeight;
    const width = targetHeight * sourceRatio;
    return { x: (targetWidth - width) / 2, y: 0, width, height };
  }

  // object-fit: cover
  if (sourceRatio > targetRatio) {
    const height = targetHeight;
    const width = targetHeight * sourceRatio;
    return { x: (targetWidth - width) / 2, y: 0, width, height };
  }

  const width = targetWidth;
  const height = targetWidth / sourceRatio;
  return { x: 0, y: (targetHeight - height) / 2, width, height };
}

function mapLandmarkToCanvas(
  landmark: NormalizedLandmark,
  rect: { x: number; y: number; width: number; height: number },
) {
  return {
    x: rect.x + landmark.x * rect.width,
    y: rect.y + landmark.y * rect.height,
  };
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

export function drawPoseFromKeypoints(
  canvas: HTMLCanvasElement,
  keypoints: BackendKeypoints | null,
  sourceWidth?: number,
  sourceHeight?: number
) {
  const context = canvas.getContext("2d");
  if (!context) return;

  syncCanvasSize(canvas);
  context.clearRect(0, 0, canvas.width, canvas.height);

  if (!keypoints || Object.keys(keypoints).length === 0) {
    drawPoseMessage(canvas, context, "未检测到人体");
    return;
  }

  context.lineCap = "round";
  context.lineJoin = "round";

  const landmarksArray: Array<{ x: number; y: number; visibility: number } | null> = new Array(33).fill(null);
  for (const [name, keypoint] of Object.entries(keypoints)) {
    const index = NAME_TO_INDEX[name];
    if (index !== undefined) {
      landmarksArray[index] = keypoint;
    }
  }

  const { scaleX, scaleY, offsetX, offsetY } = calculateFitCoverTransform(
    sourceWidth || canvas.width,
    sourceHeight || canvas.height,
    canvas.width,
    canvas.height
  );

  for (const [from, to] of BODY_CONNECTIONS) {
    const start = landmarksArray[from];
    const end = landmarksArray[to];
    if (!start || !end || start.visibility < 0.45 || end.visibility < 0.45) continue;

    const startX = (start.x * scaleX + offsetX) * canvas.width;
    const startY = (start.y * scaleY + offsetY) * canvas.height;
    const endX = (end.x * scaleX + offsetX) * canvas.width;
    const endY = (end.y * scaleY + offsetY) * canvas.height;

    context.beginPath();
    context.moveTo(startX, startY);
    context.lineTo(endX, endY);
    context.strokeStyle = "rgba(240, 178, 63, 0.96)";
    context.lineWidth = 5;
    context.shadowColor = "rgba(16, 23, 19, 0.7)";
    context.shadowBlur = 8;
    context.stroke();
  }

  context.shadowBlur = 0;
  for (const landmark of landmarksArray) {
    if (!landmark || landmark.visibility < 0.45) continue;

    const x = (landmark.x * scaleX + offsetX) * canvas.width;
    const y = (landmark.y * scaleY + offsetY) * canvas.height;
    context.beginPath();
    context.arc(x, y, 5, 0, Math.PI * 2);
    context.fillStyle = "rgba(215, 239, 227, 0.96)";
    context.fill();
    context.lineWidth = 2;
    context.strokeStyle = "rgba(18, 28, 23, 0.86)";
    context.stroke();
  }
}

function calculateFitCoverTransform(
  sourceWidth: number,
  sourceHeight: number,
  targetWidth: number,
  targetHeight: number
) {
  const sourceRatio = sourceWidth / sourceHeight;
  const targetRatio = targetWidth / targetHeight;

  let scaleX: number;
  let scaleY: number;
  let offsetX: number;
  let offsetY: number;

  if (sourceRatio > targetRatio) {
    scaleX = scaleY = targetHeight / sourceHeight;
    offsetX = (1 - scaleX * (sourceWidth / sourceHeight)) / 2;
    offsetY = 0;
  } else {
    scaleX = scaleY = targetWidth / sourceWidth;
    offsetX = 0;
    offsetY = (1 - scaleY * (sourceHeight / sourceWidth)) / 2;
  }

  return { scaleX, scaleY, offsetX, offsetY };
}

function roundPoint(value: number) {
  return Math.round(value * 10000) / 10000;
}
