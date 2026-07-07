"""Burpee analyzer — squat, plank, and jump phases with body control."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

BURPEE_STAGE_RULES = {
    "standing": {
        "hip_angle": {
            "ideal": 170, "good_range": (160, 180), "bad_range": (145, 180), "weight": 0.40,
        },
        "body_line_angle": {
            "ideal": 3, "good_range": (0, 8), "bad_range": (0, 15), "weight": 0.35,
        },
        "wrist_height": {
            "ideal": 0.02, "good_range": (0.0, 0.08), "bad_range": (0.0, 0.15), "weight": 0.25,
        },
    },
    "squat_down": {
        "hip_angle": {
            "ideal": 110, "good_range": (90, 130), "bad_range": (75, 145), "weight": 0.40,
        },
        "body_line_angle": {
            "ideal": 12, "good_range": (5, 20), "bad_range": (0, 30), "weight": 0.35,
        },
        "wrist_height": {
            "ideal": 0.12, "good_range": (0.06, 0.22), "bad_range": (0.0, 0.30), "weight": 0.25,
        },
    },
    "plank": {
        "hip_angle": {
            "ideal": 90, "good_range": (80, 105), "bad_range": (65, 120), "weight": 0.35,
        },
        "body_line_angle": {
            "ideal": 18, "good_range": (12, 25), "bad_range": (5, 35), "weight": 0.45,
        },
        "wrist_height": {
            "ideal": 0.18, "good_range": (0.10, 0.28), "bad_range": (0.04, 0.36), "weight": 0.20,
        },
    },
    "squat_up": {
        "hip_angle": {
            "ideal": 140, "good_range": (115, 165), "bad_range": (95, 175), "weight": 0.40,
        },
        "body_line_angle": {
            "ideal": 8, "good_range": (0, 15), "bad_range": (0, 25), "weight": 0.35,
        },
        "wrist_height": {
            "ideal": 0.08, "good_range": (0.02, 0.16), "bad_range": (0.0, 0.24), "weight": 0.25,
        },
    },
    "jump": {
        "hip_angle": {
            "ideal": 175, "good_range": (165, 180), "bad_range": (150, 180), "weight": 0.35,
        },
        "body_line_angle": {
            "ideal": 2, "good_range": (0, 6), "bad_range": (0, 12), "weight": 0.35,
        },
        "wrist_height": {
            "ideal": 0.22, "good_range": (0.14, 0.32), "bad_range": (0.06, 0.40), "weight": 0.30,
        },
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


class BurpeeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "burpee"

    def __init__(self, smooth_window: int = 5):
        super().__init__(smooth_window)
        self._rep_started = False
        self._seen_plank = False
        self._seen_jump = False

    def reset(self):
        super().reset()
        self._rep_started = False
        self._seen_plank = False
        self._seen_jump = False

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("squat_down", "plank", "squat_up", "jump")

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        summary = dict(samples[-1])
        hip_angles = [s["hip_angle"] for s in samples if s.get("hip_angle") is not None]
        body_lines = [s["body_line_angle"] for s in samples if s.get("body_line_angle") is not None]
        plank_lines = [
            s["body_line_angle"] for s in samples
            if s.get("body_line_angle") is not None and s.get("hip_angle", 180) <= 110
        ]
        summary["min_hip_angle"] = round(min(hip_angles), 1) if hip_angles else 180.0
        summary["max_body_line_angle"] = round(max(body_lines), 1) if body_lines else 0.0
        summary["plank_body_line_angle"] = round(max(plank_lines), 1) if plank_lines else 0.0
        wrist_heights = [s.get("wrist_height", 0) for s in samples]
        summary["max_wrist_height"] = round(max(wrist_heights), 4) if wrist_heights else 0.0
        return summary

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        squat_score = self._score_by_range(
            summary.get("min_hip_angle", 180), (85, 115), (70, 135),
        )
        plank_score = self._score_by_range(
            summary.get("plank_body_line_angle", summary.get("max_body_line_angle", 0)),
            (12, 25), (5, 35),
        )
        jump_score = self._score_by_range(
            summary.get("max_wrist_height", 0), (0.14, 0.32), (0.06, 0.40),
        )

        detail_scores = {
            "squat_depth": round(squat_score, 1),
            "plank_line": round(plank_score, 1),
            "jump_height": round(jump_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        if summary.get("min_hip_angle", 180) > 115:
            issues.append("下蹲阶段深度不足")
            feedback.append("下蹲时双手触地，髋部下沉至接近深蹲深度")
        if summary.get("plank_body_line_angle", 0) > 28:
            issues.append("平板阶段身体未保持直线")
            feedback.append("俯卧撑姿势时收紧核心，肩-髋-踝保持一条直线")
        elif summary.get("plank_body_line_angle", 0) > 22:
            issues.append("平板阶段塌腰或撅臀")
            feedback.append("平板支撑时避免髋部下沉或抬高")
        if summary.get("max_wrist_height", 0) < 0.12:
            issues.append("跳跃阶段爆发力不足")
            feedback.append("最后向上跃起时双手举过头顶，全身伸展")

        if not issues:
            feedback.append("波比跳各阶段连贯性与身体控制整体较好，继续保持")

        score = round(squat_score * 0.35 + plank_score * 0.40 + jump_score * 0.25, 1)
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
            raise ValueError("Missing keypoints for burpee analysis")

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"

        shoulder = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]
        wrist = landmarks[f"{side}_wrist"]

        hip_angle = calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )
        body_line_angle = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )
        wrist_height = hip.y - wrist.y

        return {
            "hip_angle": round(hip_angle, 1),
            "body_line_angle": round(body_line_angle, 1),
            "wrist_height": round(wrist_height, 4),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        hip = features.get("hip_angle", 170)
        body_line = features.get("body_line_angle", 3)
        wrist_h = features.get("wrist_height", 0)
        prev = state.get("prev_hip", hip)
        delta = hip - prev
        state["prev_hip"] = hip

        if hip >= 168 and wrist_h > 0.14:
            return "jump"
        if hip <= 105 and body_line >= 14:
            return "plank"
        if hip <= 125 and delta < -2:
            return "squat_down"
        if hip >= 145 and delta > 2 and body_line < 15:
            return "squat_up"
        if hip >= 158:
            return "standing"
        return "squat_down"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in BURPEE_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = BURPEE_STAGE_RULES[phase]
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

        if not issues and phase in ("plank", "jump", "standing"):
            feedback.append("波比跳该阶段控制良好，保持连贯")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    def analyze_frame(self, landmarks: Keypoints, state: dict, frame_index: int | None = None) -> dict:
        features = self.extract_features(landmarks)
        phase = self.detect_phase(features, state)
        current_stage = self.stage

        self.feature_history.append(features)
        smoothed = self._smooth_features()
        score_result = self.score_frame(smoothed, phase)

        if phase in ("squat_down", "plank"):
            self._rep_started = True
        if phase == "plank":
            self._seen_plank = True
        if phase == "jump":
            self._seen_jump = True

        if phase in self.rep_sample_phases():
            sample = dict(smoothed)
            sample["phase"] = phase
            self._rep_samples.append(sample)

        rep_completed = (
            self._rep_started
            and self._seen_plank
            and self._seen_jump
            and current_stage in ("squat_up", "jump")
            and phase == "standing"
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
            self._rep_started = False
            self._seen_plank = False
            self._seen_jump = False

        if rep_completed:
            self.count += 1
            if self._last_down_was_valid:
                self.valid_count += 1
            self.scores_history.append(frame_score)

        self.previous_stage = current_stage
        self.stage = phase

        return {
            "exercise_type": self.exercise_type,
            "phase": phase,
            "count": self.count,
            "valid_count": self.valid_count,
            "features": smoothed,
            "score": frame_score,
            "issues": frame_issues,
            "feedback": frame_feedback,
            "detail_scores": score_result.get("detail_scores", {}),
        }

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "hip_angle":
            if phase == "squat_down" and value > 125:
                return "下蹲阶段深度不足"
            if phase == "plank" and value > 110:
                return "平板阶段髋部角度偏高"
            if phase == "jump" and value < 165:
                return "跳跃阶段伸展不足"
            return "髋角控制不足"

        if name == "body_line_angle":
            if phase == "plank":
                if value > 28:
                    return "平板阶段身体未保持直线"
                if value > 22:
                    return "平板阶段塌腰或撅臀"
                return "平板阶段身体直线略有偏差"
            if phase == "squat_down" and value > 25:
                return "下蹲时躯干前倾过多"
            return "身体直线控制不足"

        if name == "wrist_height":
            if phase == "squat_down" and value < 0.08:
                return "下蹲时双手未充分触地"
            if phase == "jump" and value < 0.14:
                return "跳跃时手臂上举不足"
            return "手臂位置控制不足"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "hip_angle": {
                "squat_down": "下蹲至双手可触地，髋部充分下沉",
                "plank": "双脚后跳成平板，髋部与肩同高",
                "squat_up": "双脚跳回双手旁，准备起身",
                "jump": "全力向上跃起，髋部充分伸展",
                "standing": "落地后缓冲，准备下一次",
            },
            "body_line_angle": {
                "squat_down": "下蹲时保持背部平直",
                "plank": "收紧核心，肩-髋-踝成一直线",
                "squat_up": "起身时保持躯干稳定",
                "jump": "跳跃时身体充分伸展",
                "standing": "站立时保持核心收紧",
            },
            "wrist_height": {
                "squat_down": "下蹲时双手撑地稳定",
                "plank": "双手撑地，肩膀在手腕正上方",
                "squat_up": "双脚跳回时双手不离地",
                "jump": "跃起时双手举过头顶",
                "standing": "落地后手臂自然放下",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
