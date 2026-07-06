"""Glute-bridge analyzer — hip extension, body line, and lowering control."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)

GLUTE_BRIDGE_STAGE_RULES = {
    "lying": {
        "hip_angle": {
            "ideal": 90, "good_range": (75, 105), "bad_range": (60, 120), "weight": 0.55,
        },
        "body_line_angle": {
            "ideal": 18, "good_range": (10, 28), "bad_range": (5, 40), "weight": 0.45,
        },
    },
    "lifting": {
        "hip_angle": {
            "ideal": 130, "good_range": (110, 155), "bad_range": (90, 170), "weight": 0.50,
        },
        "body_line_angle": {
            "ideal": 10, "good_range": (4, 18), "bad_range": (0, 28), "weight": 0.50,
        },
    },
    "top_hold": {
        "hip_angle": {
            "ideal": 175, "good_range": (160, 180), "bad_range": (145, 180), "weight": 0.55,
        },
        "body_line_angle": {
            "ideal": 3, "good_range": (0, 8), "bad_range": (0, 15), "weight": 0.45,
        },
    },
    "lowering": {
        "hip_angle": {
            "ideal": 120, "good_range": (95, 150), "bad_range": (75, 165), "weight": 0.50,
        },
        "body_line_angle": {
            "ideal": 12, "good_range": (5, 20), "bad_range": (0, 30), "weight": 0.50,
        },
    },
}

REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
}


class GluteBridgeAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "glute_bridge"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("lifting", "top_hold", "lowering")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("lifting", "top_hold", "lowering"), ("lying",))

    def rep_summary_phase(self) -> str:
        return "top_hold"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        peak = dict(max(samples, key=lambda s: s.get("hip_angle", 0)))
        hip_angles = [s["hip_angle"] for s in samples if s.get("hip_angle") is not None]
        steps = [abs(c - p) for p, c in zip(hip_angles, hip_angles[1:])]
        peak["max_hip_angle_step"] = round(max(steps), 1) if steps else 0.0
        body_lines = [s["body_line_angle"] for s in samples if s.get("body_line_angle") is not None]
        peak["min_body_line_angle"] = round(min(body_lines), 1) if body_lines else 0.0
        return peak

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = GLUTE_BRIDGE_STAGE_RULES["top_hold"]
        extension_score = self._score_by_range(
            summary.get("hip_angle", 0),
            rules["hip_angle"]["good_range"],
            rules["hip_angle"]["bad_range"],
        )
        line_score = self._score_by_range(
            summary.get("min_body_line_angle", summary.get("body_line_angle", 20)),
            rules["body_line_angle"]["good_range"],
            rules["body_line_angle"]["bad_range"],
        )
        tempo_score = self._score_by_range(
            summary.get("max_hip_angle_step", 0), (0, 20), (0, 35),
        )

        detail_scores = {
            "extension": round(extension_score, 1),
            "body_line": round(line_score, 1),
            "tempo": round(tempo_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        hip = summary.get("hip_angle", 0)
        if hip < 155:
            issues.append("抬臀高度不足")
            feedback.append("顶峰收缩时肩-髋-膝尽量成一条直线，充分夹紧臀部")
        elif hip < 165:
            issues.append("髋部伸展略有不足")
            feedback.append("上抬时继续推髋至接近极限，感受臀部发力")

        body = summary.get("min_body_line_angle", summary.get("body_line_angle", 20))
        if body is not None and body > 12:
            issues.append("顶峰时身体未保持直线")
            feedback.append("收紧腹部与臀部，避免腰部过度拱起代偿")
        elif body is not None and body > 8:
            issues.append("顶峰时身体直线略有偏差")
            feedback.append("顶峰时保持肩-髋-膝一条线，不要过度挺腰")

        if summary.get("max_hip_angle_step", 0) > 32:
            issues.append("抬臀速度偏快")
            feedback.append("上抬与下放都放慢，顶峰停留 1～2 秒")

        if not issues:
            feedback.append("臀桥伸展幅度与控制整体较好，继续保持")

        score = round(extension_score * 0.50 + line_score * 0.35 + tempo_score * 0.15, 1)
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
            raise ValueError("Missing keypoints for glute bridge analysis")

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"

        shoulder = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]

        hip_angle = calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )
        body_line_angle = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )

        lk = calculate_angle(
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_hip"].to_tuple(),
            landmarks["left_knee"].to_tuple(),
        )
        rk = calculate_angle(
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_hip"].to_tuple(),
            landmarks["right_knee"].to_tuple(),
        )

        return {
            "hip_angle": round(hip_angle, 1),
            "body_line_angle": round(body_line_angle, 1),
            "hip_symmetry_diff": round(abs(lk - rk), 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        hip = features.get("hip_angle", 90)
        prev = state.get("prev_hip", hip)
        delta = hip - prev
        state["prev_hip"] = hip

        if hip >= 162 and abs(delta) <= 4:
            return "top_hold"
        if hip <= 100 and delta <= 1:
            return "lying"
        if delta > 2:
            return "lifting"
        if delta < -2:
            return "lowering"
        if hip > 130:
            return "top_hold"
        return "lying"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in GLUTE_BRIDGE_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = GLUTE_BRIDGE_STAGE_RULES[phase]
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

        sym = features.get("hip_symmetry_diff", 0)
        if sym > 15 and phase == "top_hold":
            issues.append("顶峰时左右髋部不对称")
            feedback.append("上抬时保持骨盆水平，左右均匀发力")

        if not issues and phase in ("top_hold", "lifting"):
            feedback.append("臀桥动作控制良好，保持顶峰收缩")

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "hip_angle":
            if phase == "top_hold":
                if value < 155:
                    return "顶峰抬臀高度不足"
                return "顶峰髋角略有偏差"
            if phase == "lifting" and value < 120:
                return "上抬过程中髋部发力不足"
            if phase == "lying" and value > 110:
                return "仰卧位髋角偏大"
            return "髋部角度控制不足"

        if name == "body_line_angle":
            if phase == "top_hold":
                if value > 12:
                    return "顶峰时身体未保持直线"
                if value > 8:
                    return "顶峰时腰部代偿明显"
                return "顶峰身体直线略有偏差"
            if phase == "lifting" and value > 20:
                return "上抬时腰部过度拱起"
            return "身体直线控制不足"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "hip_angle": {
                "lying": "仰卧屈膝，双脚踩实地面",
                "lifting": "臀部发力上顶，不要用腰部借力",
                "top_hold": "推髋至肩-髋-膝成直线，顶峰夹紧臀部",
                "lowering": "缓慢下放，保持核心收紧",
            },
            "body_line_angle": {
                "lifting": "上抬时保持躯干稳定，避免挺腰",
                "top_hold": "顶峰时肩-髋-膝一条线，腹部收紧",
                "lowering": "下放时保持控制，不要塌腰",
                "lying": "起始位保持骨盆中立",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
