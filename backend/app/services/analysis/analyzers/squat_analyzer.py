"""Squat analyzer — stage detection, angle computation, and per-rep scoring."""

from collections import Counter

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


SQUAT_STAGE_RULES = {
    "standing": {
        "knee_angle": {
            "ideal": 170, "good_range": (150, 180), "bad_range": (120, 180), "weight": 0.30,
        },
        "hip_angle": {
            "ideal": 170, "good_range": (140, 180), "bad_range": (110, 180), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 10, "good_range": (0, 25), "bad_range": (0, 45), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 15), "bad_range": (0, 35), "weight": 0.12,
        },
    },
    "down": {
        "knee_angle": {
            "ideal": 120, "good_range": (85, 155), "bad_range": (65, 175), "weight": 0.33,
        },
        "hip_angle": {
            "ideal": 120, "good_range": (75, 155), "bad_range": (55, 175), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20, "good_range": (5, 40), "bad_range": (0, 55), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 16), "bad_range": (0, 35), "weight": 0.12,
        },
    },
    "bottom": {
        "knee_angle": {
            "ideal": 90, "good_range": (70, 115), "bad_range": (55, 135), "weight": 0.38,
        },
        "hip_angle": {
            "ideal": 90, "good_range": (65, 125), "bad_range": (45, 145), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20, "good_range": (5, 40), "bad_range": (0, 60), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 14), "bad_range": (0, 32), "weight": 0.10,
        },
    },
    "up": {
        "knee_angle": {
            "ideal": 130, "good_range": (95, 165), "bad_range": (75, 178), "weight": 0.33,
        },
        "hip_angle": {
            "ideal": 130, "good_range": (85, 165), "bad_range": (65, 178), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 15, "good_range": (0, 35), "bad_range": (0, 55), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 16), "bad_range": (0, 35), "weight": 0.12,
        },
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


class SquatAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "squat"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        deepest = dict(min(samples, key=lambda sample: sample.get("knee_angle", 180)))
        knee_angles = [
            sample["knee_angle"]
            for sample in samples
            if sample.get("knee_angle") is not None
        ]
        steps = [
            abs(current - previous)
            for previous, current in zip(knee_angles, knee_angles[1:])
        ]
        deepest["max_knee_angle_step"] = round(max(steps), 1) if steps else 0.0
        deepest["avg_knee_angle_step"] = (
            round(sum(steps) / len(steps), 1) if steps else 0.0
        )
        return deepest

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        detail_scores: dict[str, float] = {}
        depth_score = self._score_by_range(
            summary.get("knee_angle", 180),
            SQUAT_STAGE_RULES["bottom"]["knee_angle"]["good_range"],
            SQUAT_STAGE_RULES["bottom"]["knee_angle"]["bad_range"],
        )
        trunk_score = self._score_by_range(
            summary.get("trunk_angle", 0),
            SQUAT_STAGE_RULES["bottom"]["trunk_angle"]["good_range"],
            SQUAT_STAGE_RULES["bottom"]["trunk_angle"]["bad_range"],
        )
        symmetry_score = self._score_by_range(
            summary.get("knee_symmetry_diff", 0),
            SQUAT_STAGE_RULES["bottom"]["knee_symmetry_diff"]["good_range"],
            SQUAT_STAGE_RULES["bottom"]["knee_symmetry_diff"]["bad_range"],
        )
        tempo_score = self._score_by_range(
            summary.get("max_knee_angle_step", 0),
            (0, 16),
            (0, 28),
        )

        detail_scores["depth"] = round(depth_score, 1)
        detail_scores["trunk_stability"] = round(trunk_score, 1)
        detail_scores["knee_symmetry"] = round(symmetry_score, 1)
        detail_scores["tempo"] = round(tempo_score, 1)

        issues: list[str] = []
        feedback: list[str] = []

        knee_angle = summary.get("knee_angle")
        if knee_angle is not None:
            if knee_angle > 125:
                issues.append("下蹲深度偏浅")
                feedback.append("下次下蹲到大腿接近水平即可，不要只做半蹲")
            elif knee_angle < 65:
                issues.append("下蹲深度偏深")
                feedback.append("下蹲到大腿接近水平或略低即可，避免为追求深度丢失稳定")

        trunk_angle = summary.get("trunk_angle")
        if trunk_angle is not None:
            if trunk_angle > 45:
                issues.append("底部躯干前倾明显")
                feedback.append("到底部时收紧核心、胸口微微抬起，保持背部稳定")
            elif trunk_angle > 35:
                issues.append("底部躯干前倾偏大")
                feedback.append("下蹲到底部时保持核心收紧，避免上半身继续前倒")

        knee_symmetry_diff = summary.get("knee_symmetry_diff")
        if knee_symmetry_diff is not None:
            if knee_symmetry_diff > 25:
                issues.append("底部左右膝关节明显不对称")
                feedback.append("最深处保持左右膝盖同向对齐脚尖，重心放在两脚中间")
            elif knee_symmetry_diff > 18:
                issues.append("底部左右膝关节略不对称")
                feedback.append("下蹲到底部时检查左右膝盖是否同步、同向")

        if summary.get("max_knee_angle_step", 0) > 28:
            issues.append("下蹲速度偏快")
            feedback.append("下蹲阶段放慢到约2秒，避免突然下坠")

        if not issues:
            feedback.append("深蹲深度、底部稳定性和节奏整体较好，继续保持")

        score = round(
            depth_score * 0.45
            + trunk_score * 0.25
            + symmetry_score * 0.20
            + tempo_score * 0.10,
            1,
        )
        return {
            "score": score,
            "issues": issues,
            "detail_scores": detail_scores,
            "feedback": self._dedupe(feedback),
        }

    def get_session_issue_counts(self) -> Counter[str]:
        return self._resolve_depth_conflicts(self.session_issue_counts)

    def get_session_feedback_counts(self) -> Counter[str]:
        counter = Counter(self.session_feedback_counts)
        issues = self._resolve_depth_conflicts(self.session_issue_counts)

        if "下蹲深度不稳定" in issues:
            counter.clear()
            counter["每次下蹲都控制到大腿接近水平，避免忽深忽浅"] = issues["下蹲深度不稳定"]
            for result in self.rep_results:
                for suggestion in result.get("feedback", []):
                    if "下蹲" not in suggestion and "深度" not in suggestion:
                        counter[suggestion] += 1
            return counter

        shallow_feedback = "下次下蹲到大腿接近水平即可，不要只做半蹲"
        deep_feedback = "下蹲到大腿接近水平或略低即可，避免为追求深度丢失稳定"
        if "下蹲深度偏浅" in issues:
            counter.pop(deep_feedback, None)
        if "下蹲深度偏深" in issues:
            counter.pop(shallow_feedback, None)
        return counter

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    @staticmethod
    def _resolve_depth_conflicts(counter: Counter[str]) -> Counter[str]:
        resolved = Counter(counter)
        shallow = resolved.pop("下蹲深度偏浅", 0)
        deep = resolved.pop("下蹲深度偏深", 0)

        if shallow and deep:
            if abs(shallow - deep) <= 1:
                resolved["下蹲深度不稳定"] = shallow + deep
            elif shallow > deep:
                resolved["下蹲深度偏浅"] = shallow
            else:
                resolved["下蹲深度偏深"] = deep
        elif shallow:
            resolved["下蹲深度偏浅"] = shallow
        elif deep:
            resolved["下蹲深度偏深"] = deep
        return resolved

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for squat analysis")

        # knee angle (hip → knee → ankle)
        lk = calculate_angle(
            landmarks["left_hip"].to_tuple(),
            landmarks["left_knee"].to_tuple(),
            landmarks["left_ankle"].to_tuple(),
        )
        rk = calculate_angle(
            landmarks["right_hip"].to_tuple(),
            landmarks["right_knee"].to_tuple(),
            landmarks["right_ankle"].to_tuple(),
        )
        knee_angle = (lk + rk) / 2
        knee_symmetry_diff = abs(lk - rk)

        # hip angle (shoulder → hip → knee)
        lh = calculate_angle(
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_hip"].to_tuple(),
            landmarks["left_knee"].to_tuple(),
        )
        rh = calculate_angle(
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_hip"].to_tuple(),
            landmarks["right_knee"].to_tuple(),
        )
        hip_angle = (lh + rh) / 2

        # trunk angle (shoulder-hip vs vertical)
        hip_cx = (landmarks["left_hip"].x + landmarks["right_hip"].x) / 2
        hip_cy = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
        sh_cx = (landmarks["left_shoulder"].x + landmarks["right_shoulder"].x) / 2
        sh_cy = (landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2
        trunk_angle = calculate_angle(
            (hip_cx, hip_cy - 0.1),
            (hip_cx, hip_cy),
            (sh_cx, sh_cy),
        )

        return {
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "trunk_angle": round(trunk_angle, 1),
            "knee_symmetry_diff": round(knee_symmetry_diff, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        knee = features.get("knee_angle", 170)
        prev = state.get("prev_knee", knee)
        delta = knee - prev
        state["prev_knee"] = knee

        if knee > 150:
            return "standing"
        if 65 <= knee <= 125:
            return "bottom"
        if delta < -1.5:
            return "down"
        if delta > 1.5:
            return "up"
        if knee < 145:
            return "bottom"
        return "down"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in SQUAT_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = SQUAT_STAGE_RULES[phase]
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

            # generate issues
            if s < 65:
                issues.append(self._describe_issue(name, phase, raw))
                suggestion = self._suggest_fix(name, phase, raw)
                if suggestion:
                    feedback.append(suggestion)

        knee_angle = features.get("knee_angle")
        if knee_angle is not None and phase in ("standing", "up") and knee_angle > 178:
            feedback.append("膝关节有超伸趋势，起身时保持微屈，避免锁死膝盖")

        if not issues and phase in ("bottom", "standing", "up"):
            feedback.append("动作整体标准，保持当前节奏与稳定性")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "knee_angle":
            if phase == "standing":
                return "站立时膝关节伸展不足" if value < 165 else "站立时膝关节略微屈曲"
            if phase == "down":
                if value > 150:
                    return "下蹲时膝关节弯曲不足"
                if value < 90:
                    return "下蹲时膝关节弯曲过深"
                return "下蹲时膝关节角度偏小"
            if phase == "bottom":
                if value > 120:
                    return "下蹲深度偏浅"
                if value < 75:
                    return "下蹲深度偏深"
                return "下蹲深度略有偏差"
            if phase == "up":
                return "起身时膝关节角度偏小" if value < 140 else "起身时膝关节角度偏大"

        if name == "hip_angle":
            if phase == "standing":
                return "站立时髋关节伸展不足" if value < 165 else "站立时髋关节略微屈曲"
            if phase == "down":
                if value > 150:
                    return "臀部后坐不足"
                if value < 95:
                    return "髋部折叠过快"
                return "髋部角度偏小"
            if phase == "bottom":
                if value > 120:
                    return "深蹲深度不够"
                if value < 70:
                    return "髋部下沉过深"
                return "髋部深度略有偏差"
            if phase == "up":
                return "起身时髋部发力不足" if value > 150 else "起身时髋部角度偏小"

        if name == "trunk_angle":
            if phase in ("standing", "down", "bottom", "up"):
                if value > 40:
                    return "躯干前倾明显偏大"
                if value > 30:
                    return "躯干前倾偏大"
                return "躯干前倾略大"

        if name == "knee_symmetry_diff":
            if value > 30:
                return "左右膝角差异较大"
            if value > 20:
                return "左右膝角差异偏大"
            return "左右膝角略有差异"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "knee_angle": {
                "standing": "站起时膝盖保持微屈，避免完全锁死",
                "down": "下蹲时控制速度，膝盖跟随脚尖方向",
                "bottom": "继续下沉到大腿接近水平，保持膝盖稳定",
                "up": "起身时保持膝盖稳定并对齐脚尖",
            },
            "hip_angle": {
                "standing": "收紧臀部，站直髋关节",
                "down": "臀部向后坐，保持髋部参与发力",
                "bottom": "保持髋部下沉，避免提前抬髋",
                "up": "起身时髋膝同步发力",
            },
            "trunk_angle": {
                "standing": "保持躯干挺直，避免前倾",
                "down": "胸部抬起，控制躯干角度",
                "bottom": "核心收紧，避免上半身前倒",
                "up": "起身时保持躯干稳定",
            },
            "knee_symmetry_diff": {
                "standing": "重心居中，左右膝对齐",
                "down": "左右膝同步下蹲，避免偏移",
                "bottom": "保持左右受力均衡",
                "up": "起身时保持左右发力一致",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
