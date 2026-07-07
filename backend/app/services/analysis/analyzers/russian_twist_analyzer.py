"""Russian twist analyzer — seated trunk rotation tracking."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

TWIST_STAGE_RULES = {
    "center": {
        "rotation_offset": {"good_range": (0, 0.04), "bad_range": (0, 0.10), "weight": 0.50},
        "trunk_angle": {"good_range": (15, 35), "bad_range": (5, 55), "weight": 0.50},
    },
    "left_twist": {
        "rotation_offset": {"good_range": (0.06, 0.18), "bad_range": (0.03, 0.28), "weight": 0.55},
        "trunk_angle": {"good_range": (15, 40), "bad_range": (5, 55), "weight": 0.45},
    },
    "right_twist": {
        "rotation_offset": {"good_range": (0.06, 0.18), "bad_range": (0.03, 0.28), "weight": 0.55},
        "trunk_angle": {"good_range": (15, 40), "bad_range": (5, 55), "weight": 0.45},
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder", "left_hip", "right_hip",
    "left_knee", "right_knee",
}


class RussianTwistAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "russian_twist"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("left_twist", "right_twist", "center")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("left_twist", "right_twist"), ("center",))

    def rep_summary_phase(self) -> str:
        return "left_twist"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(max(samples, key=lambda s: abs(s.get("rotation_offset", 0))))
        trunks = [s["trunk_angle"] for s in samples if s.get("trunk_angle") is not None]
        peak["avg_trunk_angle"] = round(sum(trunks) / len(trunks), 1) if trunks else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rotation_score = self._score_by_range(
            abs(summary.get("rotation_offset", 0)), (0.08, 0.20), (0.04, 0.28),
        )
        trunk_score = self._score_by_range(
            summary.get("avg_trunk_angle", summary.get("trunk_angle", 25)),
            (15, 40), (5, 55),
        )

        issues: list[str] = []
        feedback: list[str] = []
        if abs(summary.get("rotation_offset", 0)) < 0.06:
            issues.append("躯干旋转幅度不足")
            feedback.append("左右转体时尽量带动肩胛，增加旋转幅度")
        if summary.get("avg_trunk_angle", 25) < 12:
            issues.append("上身过于直立")
            feedback.append("坐姿略后仰，核心收紧后再做转体")

        score = round(rotation_score * 0.60 + trunk_score * 0.40, 1)
        if not issues:
            feedback.append("转体幅度与核心控制整体较好")

        return {
            "score": score,
            "issues": issues,
            "detail_scores": {"rotation": rotation_score, "trunk": trunk_score},
            "feedback": feedback,
        }

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints")

        ls = landmarks["left_shoulder"]
        rs = landmarks["right_shoulder"]
        lh = landmarks["left_hip"]
        rh = landmarks["right_hip"]
        lk = landmarks["left_knee"]
        rk = landmarks["right_knee"]

        sh_x = (ls.x + rs.x) / 2
        hip_x = (lh.x + rh.x) / 2
        signed_rotation = sh_x - hip_x
        rotation_offset = abs(signed_rotation)

        sh_y = (ls.y + rs.y) / 2
        hip_y = (lh.y + rh.y) / 2
        trunk_angle = calculate_angle((hip_x, hip_y - 0.1), (hip_x, hip_y), (sh_x, sh_y))

        return {
            "rotation_offset": round(rotation_offset, 4),
            "signed_rotation": round(signed_rotation, 4),
            "trunk_angle": round(trunk_angle, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        signed = features.get("signed_rotation", 0)
        if abs(signed) < 0.04:
            return "center"
        if signed < -0.05:
            return "left_twist"
        if signed > 0.05:
            return "right_twist"
        return "center"

    def score_frame(self, features: dict, phase: str) -> dict:
        rules = TWIST_STAGE_RULES.get(phase)
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
            val = abs(raw) if name == "rotation_offset" and phase != "center" else raw
            s = self._score_by_range(val, rule["good_range"], rule["bad_range"])
            detail[name] = round(s, 1)
            total += s * rule["weight"]
            weight += rule["weight"]

        if phase in ("left_twist", "right_twist") and features.get("rotation_offset", 0) < 0.06:
            issues.append("转体幅度偏小")
            feedback.append("转动时带动胸椎旋转，手肘跟随躯干移动")

        final = round(total / weight, 1) if weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": feedback}
