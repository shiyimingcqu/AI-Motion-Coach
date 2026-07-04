"""Plank analyzer for static holds with template-angle similarity scoring."""

from collections import deque
import time

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_ear", "right_ear",
}

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
        self.jitter_buffer = deque(maxlen=30)
        self.hold_scores: list[float] = []
        self._template_reference_cache: dict[str, float] | None = None

    def reset(self):
        super().reset()
        self.hold_start = None
        self.total_hold = 0.0
        self.jitter_buffer.clear()
        self.hold_scores.clear()

    def _track_frame_score(self, score_result: dict, phase: str) -> None:
        if phase in ("holding", "unstable") and score_result["score"] > 0:
            self.hold_scores.append(score_result["score"])

    def get_session_summary(self) -> dict:
        duration_seconds = int(max(self.total_hold, time.time() - self.start_time))
        average_score = (
            int(sum(self.hold_scores) / len(self.hold_scores))
            if self.hold_scores else 0
        )
        held = self.total_hold >= 5
        return {
            "exercise": self.exercise_type,
            "duration_seconds": duration_seconds,
            "total_count": 1 if held else 0,
            "valid_count": 1 if held and average_score >= 60 else 0,
            "error_count": 0 if held and average_score >= 60 else (1 if held else 0),
            "average_score": average_score,
        }

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        missing = REQUIRED - set(landmarks)
        if missing:
            raise ValueError(f"Missing keypoints: {missing}")

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"

        sh = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]
        elbow = landmarks[f"{side}_elbow"]
        ear = landmarks[f"{side}_ear"]

        body_angle = 180 - calculate_angle(sh.to_tuple(), hip.to_tuple(), ankle.to_tuple())
        hip_sag = 180 - calculate_angle(sh.to_tuple(), hip.to_tuple(), knee.to_tuple())
        elbow_offset = abs(sh.x - elbow.x)
        neck_angle = calculate_angle(ear.to_tuple(), sh.to_tuple(), hip.to_tuple())

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
        refs = self._template_references()
        ref_bl = refs.get("body_line_angle")
        ref_hip = refs.get("hip_sag", refs.get("hip_angle"))

        now = time.time()
        self.jitter_buffer.append({"bl": bl, "hip": hip, "t": now})

        if ref_bl is not None and ref_hip is not None:
            is_ready = abs(bl - ref_bl) > 35 or abs(hip - ref_hip) > 35
        else:
            is_ready = bl > 25 or hip > 30

        if is_ready:
            self.hold_start = None
            return "ready"

        if self.hold_start is None:
            self.hold_start = now
        self.total_hold = now - self.hold_start

        if len(self.jitter_buffer) >= 15:
            recent = list(self.jitter_buffer)[-15:]
            bl_var = sum((d["bl"] - bl) ** 2 for d in recent) / len(recent)
            if bl_var > 3.0:
                return "unstable"

        collapsed = abs(bl - ref_bl) > 35 if ref_bl is not None else bl > 25
        if collapsed:
            return "collapsed"

        return "holding"

    def score_frame(self, features: dict, phase: str) -> dict:
        issues: list[str] = []
        detail_scores: dict[str, float] = {}

        bl = features.get("body_line_angle", 0)
        s_bl = self._score_by_range(bl, BODY_LINE_GOOD, BODY_LINE_BAD)
        detail_scores["body_line"] = round(s_bl, 1)
        if s_bl < 60:
            issues.append("塌腰或撅臀明显，身体未保持直线")
        elif s_bl < 80:
            issues.append("身体直线略有偏差")

        hip = features.get("hip_sag", 0)
        s_hip = self._score_by_range(hip, HIP_SAG_GOOD, HIP_SAG_BAD)
        detail_scores["stability"] = round(s_hip, 1)
        if s_hip < 60:
            issues.append("髋部不稳定，核心控制不足")
        elif s_hip < 80:
            issues.append("髋部略有下沉")

        off = features.get("elbow_offset", 0)
        s_off = self._score_by_range(off, (0, 0.05), (0, 0.12))
        detail_scores["shoulder_position"] = round(s_off, 1)
        if s_off < 60:
            issues.append("肩肘位置偏差较大，支撑姿势不够稳定")

        detail_scores["duration"] = 0.0

        total = s_bl * 0.4 + s_hip * 0.3 + s_off * 0.15
        rule_score = round(total / 0.85, 1) if phase != "ready" else 0.0
        template_result = self._score_template_similarity(features)

        score = rule_score
        if template_result:
            score = template_result["score"]
            detail_scores.update(template_result["detail_scores"])
            detail_scores["rule_score"] = rule_score
            issues = template_result["issues"]

        if phase == "unstable":
            issues.append("身体晃动过大，核心控制不稳定")

        if phase != "ready" and score > 0:
            self.hold_scores.append(float(score))

        return {"score": score, "issues": issues, "detail_scores": detail_scores, "feedback": []}

    def get_session_summary(self) -> dict:
        duration_seconds = int(time.time() - self.start_time)
        active_scores = [score for score in self.hold_scores if score > 0]
        average_score = int(sum(active_scores) / len(active_scores)) if active_scores else 0
        hold_seconds = max(1, int(self.total_hold)) if active_scores else 0
        valid_seconds = hold_seconds if average_score >= 75 else 0

        return {
            "exercise": self.exercise_type,
            "duration_seconds": duration_seconds,
            "total_count": hold_seconds,
            "valid_count": valid_seconds,
            "error_count": max(0, hold_seconds - valid_seconds),
            "average_score": average_score,
        }

    def _template_references(self) -> dict[str, float]:
        if self._template_reference_cache is not None:
            return self._template_reference_cache

        try:
            template = self.template_service.load_template("plank")
        except Exception:
            self._template_reference_cache = {}
            return self._template_reference_cache

        refs: dict[str, float] = {}
        for metric, values in template.get("template_sequence", {}).items():
            numeric = [float(value) for value in values if isinstance(value, (int, float))]
            if not numeric:
                continue
            numeric = sorted(numeric)
            mid = len(numeric) // 2
            refs[metric] = (
                numeric[mid]
                if len(numeric) % 2
                else (numeric[mid - 1] + numeric[mid]) / 2
            )

        self._template_reference_cache = refs
        return refs

    def _score_template_similarity(self, features: dict) -> dict | None:
        refs = self._template_references()
        if not refs:
            return None

        aliases = {
            "hip_sag": ["hip_sag", "hip_angle"],
            "hip_angle": ["hip_angle", "hip_sag"],
        }

        try:
            template = self.template_service.load_template("plank")
            weights = template.get("weights", {})
        except Exception:
            weights = {}

        detail_scores: dict[str, float] = {}
        issues: list[str] = []
        weighted_total = 0.0
        total_weight = 0.0

        for metric, ref in refs.items():
            candidates = aliases.get(metric, [metric])
            feature_key = next((key for key in candidates if key in features), None)
            if feature_key is None:
                continue

            value = float(features[feature_key])
            diff = abs(value - ref)
            max_diff = 0.12 if metric == "elbow_offset" else 30.0
            metric_score = max(0.0, 100.0 - (diff / max_diff) * 100.0)
            weight = float(weights.get(metric, weights.get(feature_key, 0.2)))

            detail_scores[f"template_{metric}"] = round(metric_score, 1)
            weighted_total += metric_score * weight
            total_weight += weight

            if metric_score < 60:
                issues.append(f"{metric} 与标准模板差异较大")

        if not detail_scores or total_weight <= 0:
            return None

        return {
            "score": round(weighted_total / total_weight, 1),
            "detail_scores": detail_scores,
            "issues": issues,
        }
