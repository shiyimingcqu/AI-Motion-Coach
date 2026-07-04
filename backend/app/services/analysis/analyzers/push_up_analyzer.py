"""Push-up analyzer — side-view, tracks elbow/body-line angles and phase."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


PUSH_UP_STAGE_RULES = {
    "top_support": {
        "elbow_angle": {
            "ideal": 175, "good_range": (160, 180), "bad_range": (140, 180), "weight": 0.30,
        },
        "body_line_angle": {
            "ideal": 4, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.30,
        },
        "hip_sag_angle": {
            "ideal": 3, "good_range": (0, 8), "bad_range": (0, 18), "weight": 0.20,
        },
        "symmetry_diff": {
            "ideal": 0, "good_range": (0, 8), "bad_range": (0, 20), "weight": 0.20,
        },
    },
    "descending": {
        "elbow_angle": {
            "ideal": 130, "good_range": (110, 165), "bad_range": (90, 175), "weight": 0.28,
        },
        "body_line_angle": {
            "ideal": 6, "good_range": (0, 12), "bad_range": (0, 25), "weight": 0.28,
        },
        "hip_sag_angle": {
            "ideal": 5, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.22,
        },
        "symmetry_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.22,
        },
    },
    "bottom": {
        "elbow_angle": {
            "ideal": 90, "good_range": (80, 100), "bad_range": (60, 130), "weight": 0.38,
        },
        "body_line_angle": {
            "ideal": 8, "good_range": (0, 12), "bad_range": (0, 25), "weight": 0.28,
        },
        "hip_sag_angle": {
            "ideal": 6, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.18,
        },
        "symmetry_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.16,
        },
    },
    "ascending": {
        "elbow_angle": {
            "ideal": 130, "good_range": (100, 165), "bad_range": (80, 175), "weight": 0.30,
        },
        "body_line_angle": {
            "ideal": 6, "good_range": (0, 12), "bad_range": (0, 25), "weight": 0.30,
        },
        "hip_sag_angle": {
            "ideal": 5, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.20,
        },
        "symmetry_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.20,
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


class PushUpAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "push_up"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("descending", "bottom", "ascending")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("descending", "bottom"), ("ascending", "top_support"))

    def rep_summary_phase(self) -> str:
        return "bottom"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        deepest = dict(min(samples, key=lambda sample: sample.get("elbow_angle", 180)))
        elbow_angles = [
            sample["elbow_angle"]
            for sample in samples
            if sample.get("elbow_angle") is not None
        ]
        steps = [
            abs(current - previous)
            for previous, current in zip(elbow_angles, elbow_angles[1:])
        ]
        deepest["max_elbow_angle_step"] = round(max(steps), 1) if steps else 0.0
        return deepest

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = PUSH_UP_STAGE_RULES["bottom"]
        depth_score = self._score_by_range(
            summary.get("elbow_angle", 180),
            rules["elbow_angle"]["good_range"],
            rules["elbow_angle"]["bad_range"],
        )
        body_line_score = self._score_by_range(
            summary.get("body_line_angle", 0),
            rules["body_line_angle"]["good_range"],
            rules["body_line_angle"]["bad_range"],
        )
        hip_score = self._score_by_range(
            summary.get("hip_sag_angle", summary.get("hip_sag", 0)),
            rules["hip_sag_angle"]["good_range"],
            rules["hip_sag_angle"]["bad_range"],
        )
        symmetry_score = self._score_by_range(
            summary.get("symmetry_diff", 0),
            rules["symmetry_diff"]["good_range"],
            rules["symmetry_diff"]["bad_range"],
        )
        tempo_score = self._score_by_range(
            summary.get("max_elbow_angle_step", 0),
            (0, 18),
            (0, 32),
        )

        detail_scores = {
            "depth": round(depth_score, 1),
            "body_line": round(body_line_score, 1),
            "hip_stability": round(hip_score, 1),
            "symmetry": round(symmetry_score, 1),
            "tempo": round(tempo_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        elbow_angle = summary.get("elbow_angle")
        if elbow_angle is not None:
            if elbow_angle > 105:
                issues.append("下降幅度不足")
                feedback.append("下降时肘关节弯曲到接近 90°，胸部接近地面")
            elif elbow_angle < 70:
                issues.append("下降幅度过深")
                feedback.append("控制下降深度，肘关节约 90° 即可，避免过度触地")

        body_line = summary.get("body_line_angle")
        if body_line is not None and body_line > 18:
            issues.append("底部身体未保持直线")
            feedback.append("收紧核心，让肩-髋-踝保持一条直线")
        elif body_line is not None and body_line > 12:
            issues.append("底部身体直线略有偏差")
            feedback.append("避免塌腰或撅臀，保持平板姿势")

        symmetry = summary.get("symmetry_diff")
        if symmetry is not None and symmetry > 18:
            issues.append("左右发力明显不均")
            feedback.append("注意左右手均匀用力，肩膀保持水平")
        elif symmetry is not None and symmetry > 12:
            issues.append("左右略有不对称")
            feedback.append("调整手部位置，保持身体对称")

        hip_sag = summary.get("hip_sag_angle", summary.get("hip_sag"))
        if hip_sag is not None and hip_sag > 16:
            issues.append("底部髋部稳定性不足")
            feedback.append("收紧腹部与臀部，避免髋部下沉或抬高")

        if summary.get("max_elbow_angle_step", 0) > 32:
            issues.append("下降速度偏快")
            feedback.append("下降阶段放慢，控制动作节奏")

        if not issues:
            feedback.append("俯卧撑深度、身体直线和稳定性整体较好，继续保持")

        score = round(
            depth_score * 0.40
            + body_line_score * 0.25
            + hip_score * 0.15
            + symmetry_score * 0.10
            + tempo_score * 0.10,
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
        missing = REQUIRED - set(landmarks)
        if missing:
            raise ValueError(f"Missing keypoints: {missing}")

        left_vis = landmarks["left_shoulder"].visibility
        right_vis = landmarks["right_shoulder"].visibility
        side = "left" if left_vis >= right_vis else "right"

        shoulder = landmarks[f"{side}_shoulder"]
        elbow = landmarks[f"{side}_elbow"]
        wrist = landmarks[f"{side}_wrist"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]

        elbow_angle = calculate_angle(
            shoulder.to_tuple(), elbow.to_tuple(), wrist.to_tuple(),
        )
        shoulder_angle = calculate_angle(
            hip.to_tuple(), shoulder.to_tuple(), elbow.to_tuple(),
        )
        body_line_angle = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )
        hip_sag = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), knee.to_tuple(),
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
        symmetry_diff = abs(le - re)

        return {
            "elbow_angle": round(elbow_angle, 1),
            "shoulder_angle": round(shoulder_angle, 1),
            "body_line_angle": round(body_line_angle, 1),
            "hip_sag": round(hip_sag, 1),
            "hip_sag_angle": round(hip_sag, 1),
            "symmetry_diff": round(symmetry_diff, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        elbow = features.get("elbow_angle", 180)
        prev = state.get("prev_elbow", elbow)
        delta = elbow - prev
        state["prev_elbow"] = elbow

        if elbow > 150 and delta >= 0:
            return "top_support"
        if elbow > 150 and delta < -2:
            return "descending"
        if elbow <= 100:
            return "bottom"
        if 100 < elbow <= 150 and delta > 2:
            return "ascending"
        if 100 < elbow <= 150:
            return "bottom"
        return "top_support"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in PUSH_UP_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = PUSH_UP_STAGE_RULES[phase]
        total_score = 0.0
        total_weight = 0.0
        detail_scores: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None:
                continue
            score = self._score_by_range(raw, rule["good_range"], rule["bad_range"])
            detail_scores[name] = round(score, 1)
            total_score += score * rule["weight"]
            total_weight += rule["weight"]

            if score < 65:
                issues.append(self._describe_issue(name, phase, raw))
                suggestion = self._suggest_fix(name, phase, raw)
                if suggestion:
                    feedback.append(suggestion)

        if not issues and phase in ("bottom", "top_support", "ascending"):
            feedback.append("动作整体标准，保持当前节奏与稳定性")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "elbow_angle":
            if phase == "bottom":
                if value > 105:
                    return "肘关节弯曲不足，下降幅度不够"
                if value < 75:
                    return "肘关节弯曲过深"
                return "底部肘角略有偏差"
            if phase == "top_support":
                return "支撑时肘关节未充分伸展" if value < 165 else "支撑时肘角偏大"
            if phase == "descending":
                return "下降时肘部控制不足" if value > 145 else "下降节奏偏快"
            return "起身时肘部角度控制不足"

        if name == "body_line_angle":
            if value > 20:
                return "身体未保持直线（塌腰或撅臀）"
            if value > 12:
                return "身体直线略有偏差"
            return "身体直线控制略差"

        if name == "hip_sag_angle":
            if value > 18:
                return "髋部明显下沉或抬高"
            if value > 12:
                return "髋部稳定性不足"
            return "髋部控制略差"

        if name == "symmetry_diff":
            if value > 20:
                return "左右发力明显不均"
            if value > 12:
                return "左右略有不对称"
            return "左右对称性略差"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "elbow_angle": {
                "top_support": "支撑时手臂接近伸直，但不要锁死肘关节",
                "descending": "下降时控制速度，肘部贴近身体两侧",
                "bottom": "下降时肘关节弯曲到接近 90°，胸部接近地面",
                "ascending": "推起时保持肘部稳定，避免外展",
            },
            "body_line_angle": {
                "top_support": "收紧核心，保持肩-髋-踝成一直线",
                "descending": "下降过程中保持身体成平板状",
                "bottom": "底部不要塌腰或撅臀，核心持续发力",
                "ascending": "推起时保持躯干稳定，不要先抬臀",
            },
            "hip_sag_angle": {
                "top_support": "收紧腹部与臀部，稳定髋部",
                "descending": "避免臀部先行抬起或下沉",
                "bottom": "底部保持骨盆中立，核心收紧",
                "ascending": "推起时髋部与躯干同步移动",
            },
            "symmetry_diff": {
                "top_support": "双手对称放置，左右均匀发力",
                "descending": "下降时保持肩膀水平",
                "bottom": "底部检查左右手受力是否一致",
                "ascending": "推起时避免一侧先发力",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
