"""Jumping-jack analyzer — front-view, tracks arm/leg spread and synchrony."""

import math

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer,
    Keypoints,
    calculate_angle,
)


JUMPING_JACK_STAGE_RULES = {
    "closed": {
        "spread_ratio": {
            "ideal": 1.0, "good_range": (0.8, 1.6), "bad_range": (0.5, 2.5), "weight": 0.30,
        },
        "wrist_height": {
            "ideal": 0.02, "good_range": (0.0, 0.06), "bad_range": (0.0, 0.12), "weight": 0.30,
        },
        "arm_angle_diff": {
            "ideal": 0, "good_range": (0, 8), "bad_range": (0, 20), "weight": 0.20,
        },
        "shoulder_abduction_angle": {
            "ideal": 25, "good_range": (10, 45), "bad_range": (0, 70), "weight": 0.20,
        },
    },
    "opening": {
        "spread_ratio": {
            "ideal": 2.5, "good_range": (1.5, 4.0), "bad_range": (0.8, 5.5), "weight": 0.25,
        },
        "wrist_height": {
            "ideal": 0.12, "good_range": (0.06, 0.22), "bad_range": (0.0, 0.35), "weight": 0.25,
        },
        "shoulder_abduction_angle": {
            "ideal": 90, "good_range": (60, 130), "bad_range": (30, 160), "weight": 0.25,
        },
        "arm_angle_diff": {
            "ideal": 0, "good_range": (0, 12), "bad_range": (0, 30), "weight": 0.25,
        },
    },
    "open_peak": {
        "spread_ratio": {
            "ideal": 4.5, "good_range": (2.8, 5.5), "bad_range": (1.5, 6.5), "weight": 0.28,
        },
        "wrist_height": {
            "ideal": 0.25, "good_range": (0.15, 0.35), "bad_range": (0.05, 0.45), "weight": 0.28,
        },
        "shoulder_abduction_angle": {
            "ideal": 155, "good_range": (130, 175), "bad_range": (100, 180), "weight": 0.24,
        },
        "arm_angle_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 25), "weight": 0.20,
        },
    },
    "closing": {
        "spread_ratio": {
            "ideal": 2.0, "good_range": (1.2, 3.5), "bad_range": (0.6, 5.0), "weight": 0.25,
        },
        "wrist_height": {
            "ideal": 0.10, "good_range": (0.04, 0.20), "bad_range": (0.0, 0.32), "weight": 0.25,
        },
        "shoulder_abduction_angle": {
            "ideal": 70, "good_range": (40, 120), "bad_range": (15, 160), "weight": 0.25,
        },
        "arm_angle_diff": {
            "ideal": 0, "good_range": (0, 12), "bad_range": (0, 30), "weight": 0.25,
        },
    },
    "complete": {
        "spread_ratio": {
            "ideal": 1.0, "good_range": (0.8, 1.6), "bad_range": (0.5, 2.5), "weight": 0.30,
        },
        "wrist_height": {
            "ideal": 0.02, "good_range": (0.0, 0.06), "bad_range": (0.0, 0.12), "weight": 0.30,
        },
        "arm_angle_diff": {
            "ideal": 0, "good_range": (0, 8), "bad_range": (0, 20), "weight": 0.20,
        },
        "shoulder_abduction_angle": {
            "ideal": 25, "good_range": (10, 45), "bad_range": (0, 70), "weight": 0.20,
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


class JumpingJackAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "jumping_jack"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("opening", "open_peak")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("opening", "open_peak"), ("closing", "complete"))

    def rep_summary_phase(self) -> str:
        return "open_peak"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = max(samples, key=lambda sample: sample.get("spread_ratio", 0))
        spread_values = [
            sample["spread_ratio"]
            for sample in samples
            if sample.get("spread_ratio") is not None
        ]
        steps = [
            abs(current - previous)
            for previous, current in zip(spread_values, spread_values[1:])
        ]
        peak["max_spread_step"] = round(max(steps), 2) if steps else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = JUMPING_JACK_STAGE_RULES["open_peak"]
        arm_score = self._score_by_range(
            summary.get("wrist_height", summary.get("avg_arm_height", 0)),
            rules["wrist_height"]["good_range"],
            rules["wrist_height"]["bad_range"],
        )
        leg_score = self._score_by_range(
            summary.get("spread_ratio", 0),
            rules["spread_ratio"]["good_range"],
            rules["spread_ratio"]["bad_range"],
        )
        abduction_score = self._score_by_range(
            summary.get("shoulder_abduction_angle", 0),
            rules["shoulder_abduction_angle"]["good_range"],
            rules["shoulder_abduction_angle"]["bad_range"],
        )
        symmetry_score = self._score_by_range(
            summary.get("arm_angle_diff", 0),
            rules["arm_angle_diff"]["good_range"],
            rules["arm_angle_diff"]["bad_range"],
        )
        sync_score = self._score_sync(summary)

        detail_scores = {
            "arm_range": round(arm_score, 1),
            "leg_range": round(leg_score, 1),
            "abduction": round(abduction_score, 1),
            "symmetry": round(symmetry_score, 1),
            "synchrony": round(sync_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        wrist_height = summary.get("wrist_height", summary.get("avg_arm_height"))
        if wrist_height is not None and wrist_height < 0.12:
            issues.append("手臂上举幅度不足")
            feedback.append("手臂伸直上举，尽量举过头顶")
        elif wrist_height is not None and wrist_height < 0.18:
            issues.append("手臂举高幅度略不足")
            feedback.append("打开时手臂再抬高一点，形成完整幅度")

        spread = summary.get("spread_ratio")
        if spread is not None and spread < 2.5:
            issues.append("双脚打开幅度不足")
            feedback.append("双脚分开到肩宽以上，落地轻盈")
        elif spread is not None and spread < 3.2:
            issues.append("腿部展开略不足")
            feedback.append("保持膝盖与脚尖方向一致，扩大步幅")

        abduction = summary.get("shoulder_abduction_angle")
        if abduction is not None and abduction < 120:
            issues.append("肩外展角度不足")
            feedback.append("手臂向两侧充分展开，接近头顶击掌位置")

        arm_diff = summary.get("arm_angle_diff")
        if arm_diff is not None and arm_diff > 18:
            issues.append("左右动作明显不对称")
            feedback.append("保持左右手臂高度一致，减少偏差")

        if sync_score < 65:
            issues.append("手脚配合不同步")
            feedback.append("手臂上举与双脚打开同时进行，节奏一致")

        if summary.get("max_spread_step", 0) > 1.2:
            issues.append("动作节奏偏快")
            feedback.append("放慢开合节奏，保证每个阶段都到位")

        if not issues:
            feedback.append("开合跳幅度、对称性与节奏整体较好，继续保持")

        score = round(
            arm_score * 0.25
            + leg_score * 0.25
            + abduction_score * 0.15
            + symmetry_score * 0.15
            + sync_score * 0.20,
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

    @staticmethod
    def _score_sync(summary: dict[str, float]) -> float:
        arm_h = summary.get("wrist_height", summary.get("avg_arm_height", 0))
        spread = summary.get("spread_ratio", 0)
        # Normalize both to 0-100 scale for comparison
        arm_norm = min(100, max(0, arm_h / 0.30 * 100))
        leg_norm = min(100, max(0, (spread - 1.0) / 4.0 * 100))
        diff = abs(arm_norm - leg_norm)
        return round(max(0, 100 - diff * 1.2), 1)

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        missing = REQUIRED - set(landmarks)
        if missing:
            raise ValueError(f"Missing keypoints: {missing}")

        la = landmarks["left_ankle"]
        ra = landmarks["right_ankle"]
        lh = landmarks["left_hip"]
        rh = landmarks["right_hip"]
        lw = landmarks["left_wrist"]
        rw = landmarks["right_wrist"]
        ls = landmarks["left_shoulder"]
        rs = landmarks["right_shoulder"]
        le = landmarks["left_elbow"]
        re = landmarks["right_elbow"]

        foot_distance = math.hypot(la.x - ra.x, la.y - ra.y)
        hip_width = math.hypot(lh.x - rh.x, lh.y - rh.y)
        spread_ratio = foot_distance / max(hip_width, 0.01)

        left_arm_height = ls.y - lw.y
        right_arm_height = rs.y - rw.y
        wrist_height = (left_arm_height + right_arm_height) / 2

        left_arm_angle = calculate_angle(ls.to_tuple(), le.to_tuple(), lw.to_tuple())
        right_arm_angle = calculate_angle(rs.to_tuple(), re.to_tuple(), rw.to_tuple())

        left_shoulder_abduction = calculate_angle(lh.to_tuple(), ls.to_tuple(), lw.to_tuple())
        right_shoulder_abduction = calculate_angle(rh.to_tuple(), rs.to_tuple(), rw.to_tuple())

        hip_center = ((lh.x + rh.x) / 2, (lh.y + rh.y) / 2)
        leg_spread_angle = calculate_angle(la.to_tuple(), hip_center, ra.to_tuple())

        arm_height_diff = abs(left_arm_height - right_arm_height)
        arm_angle_diff = abs(left_arm_angle - right_arm_angle)
        shoulder_abduction_angle = (left_shoulder_abduction + right_shoulder_abduction) / 2

        return {
            "ankle_distance": round(foot_distance, 4),
            "foot_distance": round(foot_distance, 4),
            "spread_ratio": round(spread_ratio, 3),
            "leg_spread_angle": round(leg_spread_angle, 1),
            "wrist_height": round(wrist_height, 4),
            "avg_arm_height": round(wrist_height, 4),
            "arm_height_diff": round(arm_height_diff, 4),
            "avg_arm_angle": round((left_arm_angle + right_arm_angle) / 2, 1),
            "shoulder_abduction_angle": round(shoulder_abduction_angle, 1),
            "arm_angle_diff": round(arm_angle_diff, 1),
            "left_arm_height": round(left_arm_height, 4),
            "right_arm_height": round(right_arm_height, 4),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        foot = features.get("foot_distance", 0)
        arm_h = features.get("avg_arm_height", 0)
        spread = features.get("spread_ratio", 0)

        prev_phase = state.get("phase", "closed")
        state["phase"] = prev_phase

        if foot < 0.15 and arm_h < 0.05 and spread < 1.8:
            phase = "closed"
        elif prev_phase == "closed" and (foot >= 0.15 or arm_h >= 0.05 or spread >= 1.5):
            state["opening_foot"] = foot
            phase = "opening"
        elif spread >= 2.8 and arm_h >= 0.15:
            phase = "open_peak"
        elif prev_phase in ("open_peak", "opening") and (foot < 0.2 or spread < 2.2):
            phase = "closing"
        elif prev_phase in ("closing",) and foot < 0.15 and arm_h < 0.05:
            phase = "complete"
        else:
            phase = prev_phase

        state["phase"] = phase
        return phase

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in JUMPING_JACK_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = JUMPING_JACK_STAGE_RULES[phase]
        total_score = 0.0
        total_weight = 0.0
        detail_scores: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None and name == "wrist_height":
                raw = features.get("avg_arm_height")
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

        if phase == "open_peak":
            sync_score = self._score_sync(features)
            detail_scores["synchrony"] = sync_score
            total_score += sync_score * 0.15
            total_weight += 0.15
            if sync_score < 65:
                issues.append("手脚不同步，动作不协调")
                feedback.append("手臂上举与双脚打开同时进行")

        if not issues and phase in ("open_peak", "complete"):
            feedback.append("动作整体标准，保持当前节奏与对称性")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "spread_ratio":
            if phase == "open_peak":
                if value < 2.5:
                    return "双脚打开幅度不足"
                if value > 6.0:
                    return "双脚打开过宽，落地不稳"
                return "腿部展开幅度略有偏差"
            if phase == "closed":
                return "起始站姿未并拢" if value > 1.8 else "起始站姿控制略差"
            return "腿部展开控制不足"

        if name == "wrist_height":
            if phase == "open_peak":
                if value < 0.12:
                    return "手臂未充分举过头顶"
                return "手臂举高幅度略有不足"
            if phase == "opening":
                return "展开时手臂上举偏慢" if value < 0.08 else "展开时手臂控制略差"
            return "手臂回落控制不足"

        if name == "shoulder_abduction_angle":
            if phase == "open_peak" and value < 120:
                return "肩外展角度不足，手臂未充分展开"
            return "肩外展控制略差"

        if name == "arm_angle_diff":
            if value > 20:
                return "左右动作明显不对称"
            if value > 12:
                return "左右略有不对称"
            return "左右对称性略差"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "spread_ratio": {
                "closed": "起始时双脚并拢，身体直立",
                "opening": "展开时双脚向两侧跳开，膝盖微屈缓冲",
                "open_peak": "双脚分开到肩宽以上，落地轻盈",
                "closing": "收拢时控制落地，避免内扣",
                "complete": "回到起始站姿，准备下一次",
            },
            "wrist_height": {
                "closed": "起始时手臂自然垂于身体两侧",
                "opening": "展开时手臂同步上举",
                "open_peak": "手臂伸直上举，尽量举过头顶",
                "closing": "收拢时手臂同步下落",
                "complete": "手臂回到身体两侧",
            },
            "shoulder_abduction_angle": {
                "opening": "手臂向两侧展开，肘部微屈",
                "open_peak": "肩外展至接近 180°，手臂接近头顶",
                "closing": "收拢时保持肩外展控制",
            },
            "arm_angle_diff": {
                "opening": "左右手臂同步上举",
                "open_peak": "保持左右手臂高度一致",
                "closing": "收拢时避免一侧先下落",
                "complete": "回到对称的起始姿势",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
