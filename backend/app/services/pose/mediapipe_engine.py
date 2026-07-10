import logging
import os
import time

from app.services.pose.engine import PoseEngine

logger = logging.getLogger(__name__)


class MediaPipePoseEngine(PoseEngine):
    """MediaPipe Pose 推理引擎。

    针对小程序实时场景的鲁棒性优化：
    - 检测阈值降到 0.25（默认 0.5 对压缩小图过于严格）
    - 小图自动放大（MediaPipe 对 <320px 输入识别率明显下降）
    - 模型路径多级回退，避免单一路径缺失导致 500
    - 详细诊断日志，便于定位「未检测到人体」真因
    """

    # 实时场景下降低阈值，宁可多识别也不要漏识别
    DETECTION_CONFIDENCE = 0.25
    PRESENCE_CONFIDENCE = 0.25
    TRACKING_CONFIDENCE = 0.25
    MIN_INPUT_SIDE = 320

    def __init__(self):
        self._pose = None
        self._model_path = None
        self._infer_count = 0
        self._hit_count = 0
        self._miss_streak = 0

    def _find_model(self) -> str | None:
        """按优先级查找模型文件，全部缺失才返回 None。"""
        here = os.path.dirname(os.path.abspath(__file__))
        backend_root = os.path.realpath(os.path.join(here, "..", "..", ".."))
        candidates = [
            os.path.expanduser("~/.pose_eval/pose_landmarker.task"),
            os.path.join(backend_root, "pose_landmarker.task"),
            os.path.join(backend_root, "pose_landmarker_lite.task"),
        ]
        for path in candidates:
            real = os.path.realpath(path)
            if os.path.exists(real):
                return real
        return None

    def _ensure_pose(self):
        if self._pose is not None:
            return
        self._model_path = self._find_model()
        if not self._model_path:
            raise FileNotFoundError(
                "Pose landmarker model not found. Tried: "
                "~/.pose_eval/pose_landmarker.task, "
                "backend/pose_landmarker.task, "
                "backend/pose_landmarker_lite.task"
            )
        logger.info("[PoseEngine] 加载模型: %s", self._model_path)
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        base_options = mp_python.BaseOptions(model_asset_path=self._model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=self.DETECTION_CONFIDENCE,
            min_pose_presence_confidence=self.PRESENCE_CONFIDENCE,
            min_tracking_confidence=self.TRACKING_CONFIDENCE,
        )
        self._pose = vision.PoseLandmarker.create_from_options(options)
        logger.info(
            "[PoseEngine] 模型就绪 det=%.2f presence=%.2f tracking=%.2f min_side=%d",
            self.DETECTION_CONFIDENCE, self.PRESENCE_CONFIDENCE,
            self.TRACKING_CONFIDENCE, self.MIN_INPUT_SIDE,
        )

    def _preprocess(self, frame):
        """小图放大，提升 MediaPipe 检测率。

        前端为节省带宽常发送 256px / quality=0.4 的 JPEG，MediaPipe 对此识别率
        明显下降。放大到至少 320px 后检测率显著改善。
        """
        import cv2
        if frame is None or frame.size == 0:
            return None
        h, w = frame.shape[:2]
        longest = max(h, w)
        if longest < self.MIN_INPUT_SIDE:
            scale = float(self.MIN_INPUT_SIDE) / longest
            new_w = max(1, int(round(w * scale)))
            new_h = max(1, int(round(h * scale)))
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return frame

    def infer(self, frame):
        self._ensure_pose()
        import cv2
        import mediapipe as mp

        self._infer_count += 1
        t0 = time.time()

        if frame is None or frame.size == 0:
            logger.warning("[PoseEngine] 输入帧为空")
            return {}

        proc = self._preprocess(frame)
        if proc is None:
            return {}

        if proc.ndim == 3 and proc.shape[-1] == 3:
            rgb = cv2.cvtColor(proc, cv2.COLOR_BGR2RGB)
        else:
            rgb = proc

        try:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._pose.detect(mp_image)
        except Exception as exc:
            logger.warning("[PoseEngine] detect 异常 shape=%s: %s", rgb.shape, exc)
            return {}

        dt_ms = (time.time() - t0) * 1000.0

        if not result.pose_landmarks:
            self._miss_streak += 1
            # 连续失败或每 20 次打印一次，便于排查
            if self._miss_streak == 1 or self._infer_count % 20 == 0:
                logger.info(
                    "[PoseEngine] 未识别到人体 (累计 %d/%d, 连续%d次) "
                    "in=%dx%d proc=%dx%d 耗时=%.0fms",
                    self._infer_count - self._hit_count, self._infer_count,
                    self._miss_streak,
                    frame.shape[1], frame.shape[0],
                    rgb.shape[1], rgb.shape[0], dt_ms,
                )
            return {}

        self._hit_count += 1
        self._miss_streak = 0
        landmarks = result.pose_landmarks[0]
        if self._infer_count % 20 == 0:
            logger.info(
                "[PoseEngine] 识别成功 %d/%d %d点 耗时=%.0fms",
                self._hit_count, self._infer_count, len(landmarks), dt_ms,
            )
        return {
            str(index): {
                "x": landmark.x,
                "y": landmark.y,
                "z": landmark.z,
                "visibility": landmark.visibility,
            }
            for index, landmark in enumerate(landmarks)
        }
