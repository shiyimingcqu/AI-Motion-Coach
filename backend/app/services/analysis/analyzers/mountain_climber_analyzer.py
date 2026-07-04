"""Mountain-climber analyzer — plank base with alternating knee drives."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

MC_STAGE_RULES = {
    "plank_hold": {
        "body_line_angle": {"good_range": (0, 12), "bad_range": (0, 28), "weight": 0.40},
        "hip_angle": {"good_range": (165, 180), "bad_range": (140, 180), "weight": 0.30},
        "knee_raise": {"good_range": (0, 0.04), "bad_range": (0, 0.12), "weight": 0.30},
    },
    "left_drive": {
        "body_line_angle": {"good_range": (0, 14), "bad_range": (0, 30), "weight": 0.35},
        "knee_raise": {"good_range": (0.10, 0.30), "bad_range": (0.04, 0.40), "weight": 0.40},
        "hip_angle": {"good_range": (160, 180), "bad_range": (135, 180), "weight": 0.25},
    },
    "right_drive": {
        "body_line_angle": {"good_range": (0, 14), "bad_range": (0, 30), "weight": 0.35},
        "knee_raise": {"good_range": (0.10, 0.30), "bad_range": (0.04, 0.40), "weight": 0.40},
        "hip_angle": {"good_range": (160, 180), "bad_range": (135, 180), "weight": 0.25},
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
    "left_knee", "right_knee", "left_ankle", "right_ankle",
}


class MountainClimberAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "mountain_climber"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("left_drive", "right_drive", "plank_hold")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("left_drive", "right_drive"), ("plank_hold",))

    def rep_summary_phase(self) -> str:
        return "left_drive"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(max(samples, key=lambda s: s.get("knee_raise", 0)))
        body_lines = [s["body_line_angle"] for s in samples if s.get("body_line_angle") is not None]
        peak["max_body_line_angle"] = round(max(body_lines), 1) if body_lines else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        knee_score = self._score_by_range(
            summary.get("knee_raise", 0), (0.12, 0.28), (0.06, 0.38),
        )
        body_score = self._score_by_range(
            summary.get("max_body_line_angle", summary.get("body_line_angle", 0)),
            (0, 12), (0, 28),
        )
        hip_score = self._score_by_range(
            summary.get("hip_angle", 170), (160, 180), (140, 180),
        )

        issues: list[str] = []
        feedback: list[str] = []
        if summary.get("knee_raise", 0) < 0.10:
            issues.append("提膝高度不足")
            feedback.append("交替提膝时尽量靠近胸部，保持节奏")
        if summary.get("max_body_line_angle", 0) > 20:
            issues.append("臀部抬高，未保持平板姿势")
            feedback.append("收紧核心，肩-髋-踝保持一条直线")
        elif summary.get("max_body_line_angle", 0) > 14:
            issues.append("身体直线略有偏差")
            feedback.append("避免塌腰或撅臀，维持平板支撑姿态")

        score = round(knee_score * 0.45 + body_score * 0.35 + hip_score * 0.20, 1)
        if not issues:
            feedback.append("登山跑节奏与核心控制整体较好")

        return {
            "score": score,
            "issues": issues,
            "detail_scores": {"knee_raise": knee_score, "body_line": body_score, "hip": hip_score},
            "feedback": feedback,
        }

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints")

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"
        shoulder = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        ankle = landmarks[f"{side}_ankle"]
        knee = landmarks[f"{side}_knee"]

        body_line = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )
        hip_angle = calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )

        hy = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
        lkh = hy - landmarks["left_knee"].y
        rkh = hy - landmarks["right_knee"].y
        knee_raise = max(lkh, rkh)

        return {
            "body_line_angle": round(body_line, 1),
            "hip_angle": round(hip_angle, 1),
            "knee_raise": round(knee_raise, 4),
            "left_knee_h": round(lkh, 4),
            "right_knee_h": round(rkh, 4),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        lh = features.get("left_knee_h", 0)
        rh = features.get("right_knee_h", 0)
        if lh > 0.10 and lh >= rh:
            return "left_drive"
        if rh > 0.10:
            return "right_drive"
        return "plank_hold"

    def score_frame(self, features: dict, phase: str) -> dict:
        rules = MC_STAGE_RULES.get(phase)
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
            if s < 65 and phase == "plank_hold" and name == "body_line_angle":
                issues.append("支撑时身体未保持直线")
                feedback.append("收紧核心，避免臀部抬高或塌腰")

        final = round(total / weight, 1) if weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": feedback}
