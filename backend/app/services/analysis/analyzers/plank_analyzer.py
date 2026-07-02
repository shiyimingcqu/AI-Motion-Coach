"""Plank analyzer — static hold, tracks body-line stability and duration."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)
from collections import deque
import time


REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_ear", "right_ear",
}

# Score thresholds for static hold
BODY_LINE_GOOD = (0, 10)
BODY_LINE_BAD = (0, 25)
HIP_SAG_GOOD = (0, 12)
HIP_SAG_BAD = (0, 30)


class PlankAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "plank"

    def __init__(self, smooth_window: int = 10):
        super().__init__(smooth_window)
        self.hold_start = None
        self.total_hold = 0.0
        self.jitter_buffer = deque(maxlen=30)  # for shake detection

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        missing = REQUIRED - set(landmarks)
        if missing:
            raise ValueError(f"Missing keypoints: {missing}")

        # Use side with higher visibility
        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"

        sh = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]
        elbow = landmarks[f"{side}_elbow"]
        ear = landmarks[f"{side}_ear"]

        # 1) body-line angle (shoulder → hip → ankle) — deviation from 180°
        body_angle = 180 - calculate_angle(
            sh.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )

        # 2) hip sag (shoulder → hip → knee)
        hip_sag = 180 - calculate_angle(
            sh.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )

        # 3) shoulder-elbow offset: horizontal distance
        elbow_offset = abs(sh.x - elbow.x)

        # 4) neck angle (ear → shoulder → hip)
        neck_angle = calculate_angle(
            ear.to_tuple(), sh.to_tuple(), hip.to_tuple(),
        )

        return {
            "body_line_angle": round(body_angle, 1),
            "hip_sag": round(hip_sag, 1),
            "hip_angle": round(hip_sag, 1),
            "elbow_offset": round(elbow_offset, 3),
            "neck_angle": round(neck_angle, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        bl = features.get("body_line_angle", 0)
        hip = features.get("hip_sag", 0)

        # Accumulate jitter for shake detection
        now = time.time()
        self.jitter_buffer.append({"bl": bl, "hip": hip, "t": now})

        # Ready — large deviation means not in position yet
        if bl > 25 or hip > 30:
            self.hold_start = None
            return "ready"

        # Holding
        if self.hold_start is None:
            self.hold_start = now
        self.total_hold = now - self.hold_start

        # Shake detection via variance
        if len(self.jitter_buffer) >= 15:
            recent = list(self.jitter_buffer)[-15:]
            bl_var = sum((d["bl"] - bl) ** 2 for d in recent) / len(recent)
            if bl_var > 3.0:
                return "unstable"

        # Collapse
        if bl > 25:
            return "collapsed"

        return "holding"

    def score_frame(self, features: dict, phase: str) -> dict:
        issues: list[str] = []
        detail_scores: dict[str, float] = {}

        # --- Body line (40%) ---
        bl = features.get("body_line_angle", 0)
        s_bl = self._score_by_range(bl, BODY_LINE_GOOD, BODY_LINE_BAD)
        detail_scores["body_line"] = round(s_bl, 1)
        if s_bl < 60:
            issues.append("塌腰或撅臀明显，身体未保持直线")
        elif s_bl < 80:
            issues.append("身体直线略有偏差")

        # --- Core stability (30%) ---
        hip = features.get("hip_sag", 0)
        s_hip = self._score_by_range(hip, HIP_SAG_GOOD, HIP_SAG_BAD)
        detail_scores["stability"] = round(s_hip, 1)
        if s_hip < 60:
            issues.append("髋部不稳定，核心控制不足")
        elif s_hip < 80:
            issues.append("髋部略有下沉")

        # --- Shoulder-elbow position (15%) ---
        off = features.get("elbow_offset", 0)
        s_off = self._score_by_range(
            off, (0, 0.05), (0, 0.12),
        )
        detail_scores["shoulder_position"] = round(s_off, 1)
        if s_off < 60:
            issues.append("肩膀未在手肘正上方，姿势不正确")

        # --- Duration (15%) — scored only at the end, use placeholder ---
        detail_scores["duration"] = 0.0

        total = s_bl * 0.4 + s_hip * 0.3 + s_off * 0.15
        score = round(total / 0.85, 1) if phase != "ready" else 0

        if phase == "unstable":
            issues.append("身体晃动过大，核心控制不稳定")

        return {"score": score, "issues": issues, "detail_scores": detail_scores, "feedback": []}
