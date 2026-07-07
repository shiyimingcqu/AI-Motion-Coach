"""High-knees analyzer — knee height, rhythm, and bilateral alternation."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

HIGH_KNEES_STAGE_RULES = {
    "stand": {
        "knee_height": {
            "ideal": 0.02, "good_range": (0.0, 0.06), "bad_range": (0.0, 0.12), "weight": 0.40,
        },
        "knee_angle": {
            "ideal": 175, "good_range": (165, 180), "bad_range": (150, 180), "weight": 0.30,
        },
        "leg_height_diff": {
            "ideal": 0, "good_range": (0, 0.04), "bad_range": (0, 0.10), "weight": 0.30,
        },
    },
    "left_up": {
        "knee_height": {
            "ideal": 0.18, "good_range": (0.12, 0.28), "bad_range": (0.06, 0.36), "weight": 0.45,
        },
        "knee_angle": {
            "ideal": 95, "good_range": (75, 115), "bad_range": (55, 140), "weight": 0.30,
        },
        "leg_height_diff": {
            "ideal": 0.14, "good_range": (0.08, 0.24), "bad_range": (0.04, 0.32), "weight": 0.25,
        },
    },
    "right_up": {
        "knee_height": {
            "ideal": 0.18, "good_range": (0.12, 0.28), "bad_range": (0.06, 0.36), "weight": 0.45,
        },
        "knee_angle": {
            "ideal": 95, "good_range": (75, 115), "bad_range": (55, 140), "weight": 0.30,
        },
        "leg_height_diff": {
            "ideal": 0.14, "good_range": (0.08, 0.24), "bad_range": (0.04, 0.32), "weight": 0.25,
        },
    },
    "switch": {
        "knee_height": {
            "ideal": 0.10, "good_range": (0.05, 0.18), "bad_range": (0.0, 0.28), "weight": 0.40,
        },
        "knee_angle": {
            "ideal": 130, "good_range": (100, 160), "bad_range": (80, 175), "weight": 0.30,
        },
        "leg_height_diff": {
            "ideal": 0.08, "good_range": (0.03, 0.16), "bad_range": (0, 0.24), "weight": 0.30,
        },
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


class HighKneesAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "high_knees"

    def __init__(self, smooth_window: int = 3):
        super().__init__(smooth_window)
        self._left_hit = False
        self._right_hit = False

    def reset(self):
        super().reset()
        self._left_hit = False
        self._right_hit = False

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("left_up", "right_up", "switch")

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(max(samples, key=lambda s: s.get("knee_height", 0)))
        heights = [s["knee_height"] for s in samples if s.get("knee_height") is not None]
        steps = [abs(c - p) for p, c in zip(heights, heights[1:])]
        peak["max_height_step"] = round(max(steps), 4) if steps else 0.0
        peak["avg_knee_height"] = round(sum(heights) / len(heights), 4) if heights else 0.0
        left_h = [s.get("left_knee_h", 0) for s in samples]
        right_h = [s.get("right_knee_h", 0) for s in samples]
        peak["max_left_knee_h"] = round(max(left_h), 4) if left_h else 0.0
        peak["max_right_knee_h"] = round(max(right_h), 4) if right_h else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = HIGH_KNEES_STAGE_RULES["left_up"]
        height_score = self._score_by_range(
            summary.get("knee_height", 0),
            rules["knee_height"]["good_range"],
            rules["knee_height"]["bad_range"],
        )
        knee_score = self._score_by_range(
            summary.get("knee_angle", 180),
            rules["knee_angle"]["good_range"],
            rules["knee_angle"]["bad_range"],
        )
        sym_score = self._score_by_range(
            abs(summary.get("max_left_knee_h", 0) - summary.get("max_right_knee_h", 0)),
            (0, 0.06), (0, 0.16),
        )
        tempo_score = self._score_by_range(
            summary.get("max_height_step", 0), (0, 0.08), (0, 0.16),
        )

        detail_scores = {
            "knee_height": round(height_score, 1),
            "knee_angle": round(knee_score, 1),
            "symmetry": round(sym_score, 1),
            "tempo": round(tempo_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        kh = summary.get("knee_height", 0)
        if kh < 0.08:
            issues.append("抬膝高度不足")
            feedback.append("大腿抬至接近与地面平行，脚尖朝下")
        elif kh < 0.11:
            issues.append("抬膝高度略低")
            feedback.append("再抬高一些，膝盖尽量靠近胸部")

        left_h = summary.get("max_left_knee_h", 0)
        right_h = summary.get("max_right_knee_h", 0)
        if left_h > 0.08 and right_h > 0.08:
            diff = abs(left_h - right_h)
            if diff > 0.10:
                issues.append("左右抬膝高度明显不均")
                feedback.append("左右腿交替时保持相近的抬膝高度")
            elif diff > 0.06:
                issues.append("左右抬膝略有不对称")
                feedback.append("注意两条腿抬膝幅度一致")

        if summary.get("max_height_step", 0) > 0.14:
            issues.append("抬膝节奏不稳定")
            feedback.append("保持匀速交替，避免忽高忽低")

        if not issues:
            feedback.append("高抬腿高度、对称性与节奏整体较好，继续保持")

        score = round(
            height_score * 0.45 + knee_score * 0.20
            + sym_score * 0.20 + tempo_score * 0.15,
            1,
        )
        return {
            "score": score,
            "issues": issues,
            "detail_scores": detail_scores,
            "feedback": self._dedupe(feedback),
        }

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for high knees analysis")

        lh = landmarks["left_hip"]
        rh = landmarks["right_hip"]
        hy = (lh.y + rh.y) / 2
        lk = landmarks["left_knee"]
        rk = landmarks["right_knee"]

        left_knee_h = hy - lk.y
        right_knee_h = hy - rk.y
        knee_height = max(left_knee_h, right_knee_h)

        lka = calculate_angle(lh.to_tuple(), lk.to_tuple(), landmarks["left_ankle"].to_tuple())
        rka = calculate_angle(rh.to_tuple(), rk.to_tuple(), landmarks["right_ankle"].to_tuple())

        return {
            "knee_height": round(knee_height, 4),
            "knee_angle": round((lka + rka) / 2, 1),
            "left_knee_h": round(left_knee_h, 4),
            "right_knee_h": round(right_knee_h, 4),
            "leg_height_diff": round(abs(left_knee_h - right_knee_h), 4),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        left_h = features.get("left_knee_h", 0)
        right_h = features.get("right_knee_h", 0)
        peak_h = max(left_h, right_h)

        # 阈值按归一化坐标设置，略放宽以适配不同机位与身高
        if peak_h <= 0.07:
            return "stand"
        if left_h >= 0.08 and left_h >= right_h + 0.02:
            return "left_up"
        if right_h >= 0.08 and right_h >= left_h + 0.02:
            return "right_up"
        if left_h >= 0.08 and left_h >= right_h:
            return "left_up"
        if right_h >= 0.08:
            return "right_up"
        return "switch"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in HIGH_KNEES_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = HIGH_KNEES_STAGE_RULES[phase]
        total_score = 0.0
        total_weight = 0.0
        detail_scores: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None:
                continue
            s = self._score_by_range(raw, rule["good_range"], rule["bad_range"])
            detail_scores[name] = round(s, 1)
            total_score += s * rule["weight"]
            total_weight += rule["weight"]
            if s < 65:
                issues.append(self._describe_issue(name, phase, raw))
                suggestion = self._suggest_fix(name, phase, raw)
                if suggestion:
                    feedback.append(suggestion)

        if not issues and phase in ("left_up", "right_up"):
            feedback.append("抬膝动作到位，保持节奏")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    def analyze_frame(self, landmarks: Keypoints, state: dict) -> dict:
        features = self.extract_features(landmarks)
        phase = self.detect_phase(features, state)
        current_stage = self.stage

        self.feature_history.append(features)
        smoothed = self._smooth_features()
        score_result = self.score_frame(smoothed, phase)

        if phase == "left_up":
            self._left_hit = True
        if phase == "right_up":
            self._right_hit = True

        if phase in self.rep_sample_phases():
            self._rep_samples.append(dict(smoothed))

        rep_completed = (
            self._left_hit
            and self._right_hit
            and phase == "stand"
            and current_stage in ("left_up", "right_up", "switch", "ready")
        )

        # 单腿抬起也计次，便于实时看到反馈（完整左右交替记为有效）
        single_leg_rep = (
            phase == "stand"
            and current_stage in ("left_up", "right_up")
            and (self._left_hit or self._right_hit)
            and not (self._left_hit and self._right_hit)
        )

        frame_issues: list[str] = []
        frame_feedback: list[str] = []
        frame_score = score_result["score"]

        if rep_completed:
            rep_summary = self.summarize_rep(self._rep_samples)
            rep_result = self.score_rep(rep_summary) if rep_summary else {
                "score": 0, "issues": [], "feedback": [],
            }
            self._last_down_was_valid = len(rep_result.get("issues", [])) == 0
            frame_issues = rep_result.get("issues", [])
            frame_feedback = rep_result.get("feedback", [])
            frame_score = rep_result.get("score", frame_score)
            for issue in frame_issues:
                self.session_issue_counts[issue] += 1
            for suggestion in frame_feedback:
                self.session_feedback_counts[suggestion] += 1
            self.rep_summaries.append(rep_summary)
            self.rep_results.append(rep_result)
            self._rep_samples = []
            self._left_hit = False
            self._right_hit = False
        elif single_leg_rep:
            self._last_down_was_valid = len(score_result.get("issues", [])) == 0
            frame_issues = score_result.get("issues", [])
            frame_feedback = score_result.get("feedback", [])
            frame_score = score_result.get("score", frame_score)

        if rep_completed or single_leg_rep:
            self.count += 1
            if rep_completed and self._last_down_was_valid:
                self.valid_count += 1
            elif single_leg_rep and self._last_down_was_valid:
                self.valid_count += 1
            self.scores_history.append(frame_score)
            if single_leg_rep and not rep_completed:
                # 完成一侧后重置，等待另一侧
                if current_stage == "left_up":
                    self._left_hit = False
                elif current_stage == "right_up":
                    self._right_hit = False

        self.previous_stage = current_stage
        self.stage = phase

        return {
            "exercise_type": self.exercise_type,
            "phase": phase,
            "stage": phase,
            "count": self.count,
            "valid_count": self.valid_count,
            "features": smoothed,
            "metrics": smoothed,
            "score": frame_score,
            "issues": frame_issues,
            "errors": frame_issues,
            "feedback": frame_feedback,
            "detail_scores": score_result.get("detail_scores", {}),
        }

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "knee_height":
            if phase in ("left_up", "right_up"):
                if value < 0.08:
                    return "抬膝高度不足"
                if value < 0.11:
                    return "抬膝高度略低"
                return "抬膝高度略有偏差"
            return "支撑时膝位偏高"

        if name == "knee_angle":
            if phase in ("left_up", "right_up") and value > 120:
                return "抬膝时大腿折叠不足"
            return "膝角控制略有偏差"

        if name == "leg_height_diff":
            if phase == "switch" and value < 0.04:
                return "左右交替不明显"
            if phase in ("left_up", "right_up") and value < 0.08:
                return "支撑腿未充分伸直"
            return "左右腿高度差异常"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "knee_height": {
                "left_up": "左膝抬至大腿接近水平，积极摆臂配合",
                "right_up": "右膝抬至大腿接近水平，保持上身直立",
                "switch": "交替时保持抬膝幅度",
                "stand": "支撑腿稳定，准备下一次抬膝",
            },
            "knee_angle": {
                "left_up": "左膝抬高时大腿尽量平行地面",
                "right_up": "右膝抬高时大腿尽量平行地面",
                "switch": "转换时保持核心收紧",
                "stand": "站立时保持轻微屈膝缓冲",
            },
            "leg_height_diff": {
                "left_up": "左膝抬起时右支撑腿尽量伸直",
                "right_up": "右膝抬起时左支撑腿尽量伸直",
                "switch": "左右交替幅度保持一致",
                "stand": "双脚交替时保持重心稳定",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
