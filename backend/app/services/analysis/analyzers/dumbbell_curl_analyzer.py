"""Dumbbell curl analyzer — elbow flexion with upper-arm stability."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

CURL_STAGE_RULES = {
    "extended": {
        "elbow_angle": {"good_range": (155, 180), "bad_range": (130, 180), "weight": 0.55},
        "shoulder_angle": {"good_range": (5, 25), "bad_range": (0, 45), "weight": 0.45},
    },
    "curling": {
        "elbow_angle": {"good_range": (80, 140), "bad_range": (50, 170), "weight": 0.50},
        "shoulder_angle": {"good_range": (5, 30), "bad_range": (0, 50), "weight": 0.50},
    },
    "peak": {
        "elbow_angle": {"good_range": (30, 55), "bad_range": (15, 80), "weight": 0.55},
        "shoulder_angle": {"good_range": (5, 30), "bad_range": (0, 55), "weight": 0.45},
    },
    "lowering": {
        "elbow_angle": {"good_range": (80, 150), "bad_range": (50, 175), "weight": 0.50},
        "shoulder_angle": {"good_range": (5, 30), "bad_range": (0, 50), "weight": 0.50},
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
}


class DumbbellCurlAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "dumbbell_curl"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("curling", "peak", "lowering")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("curling", "peak", "lowering"), ("extended",))

    def rep_summary_phase(self) -> str:
        return "peak"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(min(samples, key=lambda s: s.get("elbow_angle", 180)))
        shoulders = [s["shoulder_angle"] for s in samples if s.get("shoulder_angle") is not None]
        peak["max_shoulder_angle"] = round(max(shoulders), 1) if shoulders else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        curl_score = self._score_by_range(
            summary.get("elbow_angle", 180), (30, 55), (15, 90),
        )
        stability_score = self._score_by_range(
            summary.get("max_shoulder_angle", 0), (5, 30), (0, 55),
        )

        issues: list[str] = []
        feedback: list[str] = []
        if summary.get("elbow_angle", 180) > 70:
            issues.append("弯举顶峰收缩不足")
            feedback.append("上举至前臂接近垂直，感受肱二头肌顶峰收缩")
        if summary.get("max_shoulder_angle", 0) > 40:
            issues.append("上臂前移或身体借力")
            feedback.append("上臂贴近身体固定，避免摆动借力")

        score = round(curl_score * 0.60 + stability_score * 0.40, 1)
        if not issues:
            feedback.append("弯举幅度与上臂稳定性整体较好")

        return {
            "score": score,
            "issues": issues,
            "detail_scores": {"curl_depth": curl_score, "stability": stability_score},
            "feedback": feedback,
        }

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints")

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"
        shoulder = landmarks[f"{side}_shoulder"]
        elbow = landmarks[f"{side}_elbow"]
        wrist = landmarks[f"{side}_wrist"]
        hip = landmarks[f"{side}_hip"]

        elbow_angle = calculate_angle(
            shoulder.to_tuple(), elbow.to_tuple(), wrist.to_tuple(),
        )
        shoulder_angle = calculate_angle(
            hip.to_tuple(), shoulder.to_tuple(), elbow.to_tuple(),
        )

        le = calculate_angle(
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_elbow"].to_tuple(),
            landmarks["left_wrist"].to_tuple(),
        )
        re = calculate_angle(
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_elbow"].to_tuple(),
            landmarks["right_wrist"].to_tuple(),
        )

        return {
            "elbow_angle": round(elbow_angle, 1),
            "shoulder_angle": round(shoulder_angle, 1),
            "symmetry_diff": round(abs(le - re), 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        elbow = features.get("elbow_angle", 180)
        prev = state.get("prev_elbow", elbow)
        delta = elbow - prev
        state["prev_elbow"] = elbow

        if elbow > 150 and delta >= 0:
            return "extended"
        if elbow > 150 and delta < -2:
            return "curling"
        if elbow <= 60:
            return "peak"
        if 60 < elbow <= 150 and delta > 2:
            return "lowering"
        return "curling"

    def score_frame(self, features: dict, phase: str) -> dict:
        rules = CURL_STAGE_RULES.get(phase)
        if not rules:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        total = 0.0
        weight = 0.0
        detail: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None:
                continue
            s = self._score_by_range(raw, rule["good_range"], rule["bad_range"])
            detail[name] = round(s, 1)
            total += s * rule["weight"]
            weight += rule["weight"]

        if features.get("shoulder_angle", 0) > 45:
            issues.append("上臂未固定，存在借力")
            feedback.append("保持上臂垂直固定，仅前臂完成弯举")

        final = round(total / weight, 1) if weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": feedback}
