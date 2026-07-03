"""Lunge analyzer — front-leg depth, trunk control, and bilateral symmetry."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

LUNGE_STAGE_RULES = {
    "standing": {
        "knee_angle": {
            "ideal": 170, "good_range": (155, 180), "bad_range": (130, 180), "weight": 0.30,
        },
        "hip_angle": {
            "ideal": 175, "good_range": (160, 180), "bad_range": (140, 180), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 5, "good_range": (0, 12), "bad_range": (0, 25), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 12), "bad_range": (0, 30), "weight": 0.20,
        },
    },
    "down": {
        "knee_angle": {
            "ideal": 120, "good_range": (95, 145), "bad_range": (75, 165), "weight": 0.35,
        },
        "hip_angle": {
            "ideal": 140, "good_range": (115, 160), "bad_range": (95, 175), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 12, "good_range": (5, 20), "bad_range": (0, 32), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 8, "good_range": (0, 20), "bad_range": (0, 40), "weight": 0.15,
        },
    },
    "bottom": {
        "knee_angle": {
            "ideal": 90, "good_range": (75, 105), "bad_range": (60, 120), "weight": 0.38,
        },
        "hip_angle": {
            "ideal": 105, "good_range": (85, 125), "bad_range": (70, 140), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 15, "good_range": (8, 22), "bad_range": (0, 35), "weight": 0.22,
        },
        "knee_symmetry_diff": {
            "ideal": 10, "good_range": (0, 22), "bad_range": (0, 42), "weight": 0.15,
        },
    },
    "up": {
        "knee_angle": {
            "ideal": 130, "good_range": (100, 160), "bad_range": (80, 175), "weight": 0.33,
        },
        "hip_angle": {
            "ideal": 150, "good_range": (125, 170), "bad_range": (105, 178), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 10, "good_range": (0, 18), "bad_range": (0, 30), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 15), "bad_range": (0, 35), "weight": 0.17,
        },
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


class LungeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "lunge"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("down", "bottom", "up")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("down", "bottom"), ("up", "standing"))

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        deepest = dict(min(samples, key=lambda s: s.get("knee_angle", 180)))
        knee_angles = [s["knee_angle"] for s in samples if s.get("knee_angle") is not None]
        steps = [
            abs(cur - prev) for prev, cur in zip(knee_angles, knee_angles[1:])
        ]
        deepest["max_knee_angle_step"] = round(max(steps), 1) if steps else 0.0
        trunk_angles = [s["trunk_angle"] for s in samples if s.get("trunk_angle") is not None]
        deepest["max_trunk_angle"] = round(max(trunk_angles), 1) if trunk_angles else 0.0
        sym = [s["knee_symmetry_diff"] for s in samples if s.get("knee_symmetry_diff") is not None]
        deepest["max_knee_symmetry_diff"] = round(max(sym), 1) if sym else 0.0
        return deepest

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = LUNGE_STAGE_RULES["bottom"]
        depth_score = self._score_by_range(
            summary.get("knee_angle", 180),
            rules["knee_angle"]["good_range"],
            rules["knee_angle"]["bad_range"],
        )
        trunk_score = self._score_by_range(
            summary.get("max_trunk_angle", summary.get("trunk_angle", 0)),
            rules["trunk_angle"]["good_range"],
            rules["trunk_angle"]["bad_range"],
        )
        symmetry_score = self._score_by_range(
            summary.get("max_knee_symmetry_diff", summary.get("knee_symmetry_diff", 0)),
            rules["knee_symmetry_diff"]["good_range"],
            rules["knee_symmetry_diff"]["bad_range"],
        )
        tempo_score = self._score_by_range(
            summary.get("max_knee_angle_step", 0), (0, 18), (0, 32),
        )

        detail_scores = {
            "depth": round(depth_score, 1),
            "trunk_stability": round(trunk_score, 1),
            "knee_symmetry": round(symmetry_score, 1),
            "tempo": round(tempo_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        knee = summary.get("knee_angle")
        if knee is not None:
            if knee > 105:
                issues.append("弓步下蹲深度不足")
                feedback.append("前腿屈膝至约 90°，后腿膝盖接近地面")
            elif knee < 70:
                issues.append("弓步下蹲过深")
                feedback.append("控制下蹲深度，前腿约 90° 即可，避免膝盖压力过大")

        trunk = summary.get("max_trunk_angle", summary.get("trunk_angle"))
        if trunk is not None:
            if trunk > 28:
                issues.append("躯干前倾明显过多")
                feedback.append("保持上身挺直，核心收紧，避免过度前倾")
            elif trunk > 22:
                issues.append("躯干前倾偏大")
                feedback.append("下蹲时胸口微抬，减少身体向前倾倒")

        sym = summary.get("max_knee_symmetry_diff", summary.get("knee_symmetry_diff"))
        if sym is not None and sym > 25:
            issues.append("前后腿弯曲明显不对称")
            feedback.append("注意前腿弯曲更多、后腿接近伸直，保持弓步形态")
        elif sym is not None and sym > 18:
            issues.append("左右膝角差异偏大")
            feedback.append("检查前腿是否承担主要弯曲，后腿保持相对稳定")

        if summary.get("max_knee_angle_step", 0) > 30:
            issues.append("下蹲速度偏快")
            feedback.append("下蹲阶段放慢，控制前腿弯曲节奏")

        if not issues:
            feedback.append("弓步蹲深度、躯干稳定与对称性整体较好，继续保持")

        score = round(
            depth_score * 0.45 + trunk_score * 0.25
            + symmetry_score * 0.20 + tempo_score * 0.10,
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
            raise ValueError("Missing keypoints for lunge analysis")

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
        knee_angle = min(lk, rk)

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

        hip_cx = (landmarks["left_hip"].x + landmarks["right_hip"].x) / 2
        hip_cy = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
        sh_cx = (landmarks["left_shoulder"].x + landmarks["right_shoulder"].x) / 2
        sh_cy = (landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2
        trunk_angle = calculate_angle(
            (hip_cx, hip_cy - 0.1), (hip_cx, hip_cy), (sh_cx, sh_cy),
        )

        return {
            "knee_angle": round(knee_angle, 1),
            "hip_angle": round(hip_angle, 1),
            "trunk_angle": round(trunk_angle, 1),
            "knee_symmetry_diff": round(abs(lk - rk), 1),
            "front_knee_angle": round(knee_angle, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        knee = features.get("knee_angle", 170)
        prev = state.get("prev_knee", knee)
        delta = knee - prev
        state["prev_knee"] = knee

        if knee > 155:
            return "standing"
        if 70 <= knee <= 110 and abs(delta) <= 4:
            return "bottom"
        if delta < -2:
            return "down"
        if delta > 2:
            return "up"
        return "down"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in LUNGE_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = LUNGE_STAGE_RULES[phase]
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

        if not issues and phase in ("bottom", "standing", "up"):
            feedback.append("弓步姿态整体稳定，保持当前节奏")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "knee_angle":
            if phase == "bottom":
                if value > 105:
                    return "弓步底部深度不足"
                if value < 75:
                    return "弓步底部下蹲过深"
                return "弓步底部膝角略有偏差"
            if phase == "down" and value > 140:
                return "下蹲时前腿弯曲不足"
            if phase == "standing" and value < 165:
                return "站立时前腿未充分伸展"
            return "前腿膝角控制不足"

        if name == "trunk_angle":
            if value > 28:
                return "躯干前倾明显过多"
            if value > 20:
                return "躯干前倾偏大"
            return "躯干控制略有偏差"

        if name == "knee_symmetry_diff":
            if value > 30:
                return "前后腿弯曲差异过大"
            if value > 22:
                return "前后腿弯曲不对称"
            return "膝角对称性略差"

        if name == "hip_angle":
            if phase == "bottom" and value > 125:
                return "髋部下沉不足"
            return "髋部角度控制不足"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "knee_angle": {
                "down": "向前跨步后，前腿屈膝下沉，后腿自然弯曲",
                "bottom": "前腿屈膝至约 90°，膝盖对齐脚尖方向",
                "up": "前腿发力蹬起，保持躯干稳定",
                "standing": "站起时前腿接近伸直，准备换腿或下一次",
            },
            "trunk_angle": {
                "down": "下蹲时保持胸口微抬，避免上身过度前倒",
                "bottom": "底部收紧核心，上身尽量垂直",
                "up": "起身时躯干与髋部同步上移",
                "standing": "站立时保持背部挺直",
            },
            "knee_symmetry_diff": {
                "down": "前腿承担主要弯曲，后腿保持稳定",
                "bottom": "检查前腿弯曲是否明显大于后腿",
                "up": "起身时避免一侧腿先发力",
                "standing": "换腿前检查左右弓步对称性",
            },
            "hip_angle": {
                "bottom": "髋部随前腿下沉，保持弓步形态",
                "down": "臀部略下沉，配合前腿弯曲",
                "up": "髋部与前腿同步推起",
                "standing": "站直时髋部中立",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
