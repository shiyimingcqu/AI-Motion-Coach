"""Dumbbell press analyzer — shoulder press with elbow tracking."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

PRESS_STAGE_RULES = {
    "bottom": {
        "elbow_angle": {"good_range": (70, 100), "bad_range": (50, 120), "weight": 0.50},
        "shoulder_angle": {"good_range": (70, 110), "bad_range": (50, 140), "weight": 0.50},
    },
    "pressing": {
        "elbow_angle": {"good_range": (100, 150), "bad_range": (70, 175), "weight": 0.50},
        "shoulder_angle": {"good_range": (90, 140), "bad_range": (60, 160), "weight": 0.50},
    },
    "top": {
        "elbow_angle": {"good_range": (155, 180), "bad_range": (130, 180), "weight": 0.50},
        "shoulder_angle": {"good_range": (150, 180), "bad_range": (120, 180), "weight": 0.50},
    },
    "lowering": {
        "elbow_angle": {"good_range": (100, 150), "bad_range": (70, 175), "weight": 0.50},
        "shoulder_angle": {"good_range": (90, 140), "bad_range": (60, 160), "weight": 0.50},
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
}


class DumbbellPressAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "dumbbell_press"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("pressing", "top", "lowering")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("pressing", "top", "lowering"), ("bottom",))

    def rep_summary_phase(self) -> str:
        return "top"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(max(samples, key=lambda s: s.get("elbow_angle", 0)))
        shoulders = [s["shoulder_angle"] for s in samples if s.get("shoulder_angle") is not None]
        peak["max_shoulder_angle"] = round(max(shoulders), 1) if shoulders else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        extension_score = self._score_by_range(
            summary.get("elbow_angle", 0), (155, 180), (130, 180),
        )
        shoulder_score = self._score_by_range(
            summary.get("max_shoulder_angle", 0), (150, 180), (120, 180),
        )

        issues: list[str] = []
        feedback: list[str] = []
        if summary.get("elbow_angle", 0) < 150:
            issues.append("推举未充分伸直")
            feedback.append("上推至手臂接近伸直，但不要锁死肘关节")
        if summary.get("symmetry_diff", 0) > 20:
            issues.append("左右推举不对称")
            feedback.append("双手同步上推，保持哑铃轨迹对称")

        score = round(extension_score * 0.55 + shoulder_score * 0.45, 1)
        if not issues:
            feedback.append("推举幅度与对称性整体较好")

        return {
            "score": score,
            "issues": issues,
            "detail_scores": {"extension": extension_score, "shoulder": shoulder_score},
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
        elbow = features.get("elbow_angle", 90)
        prev = state.get("prev_elbow", elbow)
        delta = elbow - prev
        state["prev_elbow"] = elbow

        if elbow < 105 and delta <= 0:
            return "bottom"
        if elbow < 105 and delta > 2:
            return "pressing"
        if elbow >= 155:
            return "top"
        if 105 <= elbow < 155 and delta < -2:
            return "lowering"
        return "pressing"

    def score_frame(self, features: dict, phase: str) -> dict:
        rules = PRESS_STAGE_RULES.get(phase)
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

        if phase == "top" and features.get("elbow_angle", 0) < 150:
            issues.append("顶峰时手臂未充分伸展")
            feedback.append("推举至手臂接近伸直，感受肩部发力")

        final = round(total / weight, 1) if weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": feedback}
