"""Pull-up analyzer — tracks elbow flexion and body control."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

PULL_UP_STAGE_RULES = {
    "hanging": {
        "elbow_angle": {"good_range": (160, 180), "bad_range": (140, 180), "weight": 0.50},
        "body_line_angle": {"good_range": (0, 10), "bad_range": (0, 25), "weight": 0.50},
    },
    "pulling": {
        "elbow_angle": {"good_range": (90, 150), "bad_range": (60, 175), "weight": 0.55},
        "body_line_angle": {"good_range": (0, 12), "bad_range": (0, 28), "weight": 0.45},
    },
    "top": {
        "elbow_angle": {"good_range": (60, 100), "bad_range": (40, 130), "weight": 0.55},
        "body_line_angle": {"good_range": (0, 12), "bad_range": (0, 28), "weight": 0.45},
    },
    "lowering": {
        "elbow_angle": {"good_range": (100, 165), "bad_range": (70, 180), "weight": 0.50},
        "body_line_angle": {"good_range": (0, 12), "bad_range": (0, 28), "weight": 0.50},
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_hip", "right_hip",
}


class PullUpAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "pull_up"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("pulling", "top", "lowering")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("pulling", "top", "lowering"), ("hanging",))

    def rep_summary_phase(self) -> str:
        return "top"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(min(samples, key=lambda s: s.get("elbow_angle", 180)))
        body_lines = [s["body_line_angle"] for s in samples if s.get("body_line_angle") is not None]
        peak["max_body_line_angle"] = round(max(body_lines), 1) if body_lines else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        depth_score = self._score_by_range(
            summary.get("elbow_angle", 180), (70, 100), (50, 130),
        )
        body_score = self._score_by_range(
            summary.get("max_body_line_angle", 0), (0, 12), (0, 28),
        )

        issues: list[str] = []
        feedback: list[str] = []
        elbow = summary.get("elbow_angle", 180)
        if elbow > 105:
            issues.append("上拉幅度不足")
            feedback.append("拉起时尽量让下巴接近横杆，肘部充分弯曲")
        if summary.get("max_body_line_angle", 0) > 20:
            issues.append("身体摆动借力明显")
            feedback.append("收紧核心，避免借力摆动，控制上拉与下放")

        score = round(depth_score * 0.65 + body_score * 0.35, 1)
        if not issues:
            feedback.append("引体向上幅度与控制整体较好")

        return {
            "score": score,
            "issues": issues,
            "detail_scores": {"depth": depth_score, "body_control": body_score},
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
        body_line = abs(shoulder.x - hip.x) * 100

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
            "body_line_angle": round(body_line, 1),
            "symmetry_diff": round(abs(le - re), 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        elbow = features.get("elbow_angle", 180)
        prev = state.get("prev_elbow", elbow)
        delta = elbow - prev
        state["prev_elbow"] = elbow

        if elbow > 155 and delta >= 0:
            return "hanging"
        if elbow > 155 and delta < -2:
            return "pulling"
        if elbow <= 100:
            return "top"
        if 100 < elbow <= 155 and delta > 2:
            return "lowering"
        return "pulling"

    def score_frame(self, features: dict, phase: str) -> dict:
        rules = PULL_UP_STAGE_RULES.get(phase)
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

        if phase == "top" and features.get("elbow_angle", 180) > 105:
            issues.append("顶峰时肘部弯曲不足")
            feedback.append("拉到最高点时肘部充分弯曲，下巴尽量过杆")

        final = round(total / weight, 1) if weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": feedback}
