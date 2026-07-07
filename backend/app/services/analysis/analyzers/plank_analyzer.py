"""Plank analyzer — static hold, tracks body-line stability and duration."""

import time
from collections import deque

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


PLANK_STAGE_RULES = {
    "ready": {
        "body_line_angle": {
            "ideal": 15, "good_range": (0, 25), "bad_range": (0, 45), "weight": 0.35,
        },
        "hip_sag_angle": {
            "ideal": 15, "good_range": (0, 25), "bad_range": (0, 40), "weight": 0.30,
        },
        "elbow_offset": {
            "ideal": 0.04, "good_range": (0, 0.08), "bad_range": (0, 0.15), "weight": 0.20,
        },
        "neck_angle": {
            "ideal": 55, "good_range": (45, 70), "bad_range": (30, 90), "weight": 0.15,
        },
    },
    "holding": {
        "body_line_angle": {
            "ideal": 5, "good_range": (0, 10), "bad_range": (0, 22), "weight": 0.35,
        },
        "hip_sag_angle": {
            "ideal": 6, "good_range": (0, 12), "bad_range": (0, 25), "weight": 0.30,
        },
        "elbow_offset": {
            "ideal": 0.03, "good_range": (0, 0.05), "bad_range": (0, 0.12), "weight": 0.20,
        },
        "neck_angle": {
            "ideal": 55, "good_range": (48, 65), "bad_range": (35, 85), "weight": 0.15,
        },
    },
    "unstable": {
        "body_line_angle": {
            "ideal": 8, "good_range": (0, 14), "bad_range": (0, 25), "weight": 0.35,
        },
        "hip_sag_angle": {
            "ideal": 10, "good_range": (0, 16), "bad_range": (0, 28), "weight": 0.30,
        },
        "elbow_offset": {
            "ideal": 0.03, "good_range": (0, 0.06), "bad_range": (0, 0.14), "weight": 0.20,
        },
        "neck_angle": {
            "ideal": 55, "good_range": (45, 68), "bad_range": (32, 88), "weight": 0.15,
        },
    },
    "collapsed": {
        "body_line_angle": {
            "ideal": 20, "good_range": (0, 30), "bad_range": (0, 50), "weight": 0.40,
        },
        "hip_sag_angle": {
            "ideal": 20, "good_range": (0, 30), "bad_range": (0, 45), "weight": 0.35,
        },
        "elbow_offset": {
            "ideal": 0.05, "good_range": (0, 0.10), "bad_range": (0, 0.18), "weight": 0.25,
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
    "left_ear", "right_ear",
}


class PlankAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "plank"

    def __init__(self, smooth_window: int = 10):
        super().__init__(smooth_window)
        self.hold_start = None
        self.total_hold = 0.0
        self.jitter_buffer = deque(maxlen=30)

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("holding",)

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        # Static hold — no rep counting
        return ((), ())

    def rep_summary_phase(self) -> str:
        return "holding"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        worst = dict(max(samples, key=lambda sample: sample.get("body_line_angle", 0)))
        worst["hip_sag_angle"] = max(
            sample.get("hip_sag_angle", sample.get("hip_sag", 0))
            for sample in samples
        )
        body_values = [
            sample["body_line_angle"]
            for sample in samples
            if sample.get("body_line_angle") is not None
        ]
        if len(body_values) >= 2:
            steps = [
                abs(current - previous)
                for previous, current in zip(body_values, body_values[1:])
            ]
            worst["max_body_jitter"] = round(max(steps), 1) if steps else 0.0
        else:
            worst["max_body_jitter"] = 0.0
        return worst

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = PLANK_STAGE_RULES["holding"]
        body_score = self._score_by_range(
            summary.get("body_line_angle", 0),
            rules["body_line_angle"]["good_range"],
            rules["body_line_angle"]["bad_range"],
        )
        hip_score = self._score_by_range(
            summary.get("hip_sag_angle", summary.get("hip_sag", 0)),
            rules["hip_sag_angle"]["good_range"],
            rules["hip_sag_angle"]["bad_range"],
        )
        elbow_score = self._score_by_range(
            summary.get("elbow_offset", 0),
            rules["elbow_offset"]["good_range"],
            rules["elbow_offset"]["bad_range"],
        )
        jitter_score = self._score_by_range(
            summary.get("max_body_jitter", 0),
            (0, 4),
            (0, 10),
        )

        detail_scores = {
            "body_line": round(body_score, 1),
            "stability": round(hip_score, 1),
            "shoulder_position": round(elbow_score, 1),
            "control": round(jitter_score, 1),
        }

        issues: list[str] = []
        feedback: list[str] = []

        body_line = summary.get("body_line_angle")
        if body_line is not None and body_line > 18:
            issues.append("塌腰或撅臀明显，身体未保持直线")
            feedback.append("收紧核心，保持肩-髋-踝成一直线")
        elif body_line is not None and body_line > 12:
            issues.append("身体直线略有偏差")
            feedback.append("轻微调整髋部位置，维持直线")

        hip_sag = summary.get("hip_sag_angle", summary.get("hip_sag"))
        if hip_sag is not None and hip_sag > 20:
            issues.append("髋部不稳定，核心控制不足")
            feedback.append("收紧腹部与臀部，避免髋部下沉")
        elif hip_sag is not None and hip_sag > 14:
            issues.append("髋部略有下沉")
            feedback.append("保持骨盆中立，核心持续发力")

        if summary.get("max_body_jitter", 0) > 8:
            issues.append("支撑过程中晃动过大")
            feedback.append("放慢呼吸，保持稳定支撑")

        if not issues:
            feedback.append("平板支撑姿态稳定，核心控制较好，继续保持")

        score = round(
            body_score * 0.40
            + hip_score * 0.30
            + elbow_score * 0.15
            + jitter_score * 0.15,
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

        lv = landmarks["left_shoulder"].visibility
        rv = landmarks["right_shoulder"].visibility
        side = "left" if lv >= rv else "right"

        sh = landmarks[f"{side}_shoulder"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]
        elbow = landmarks[f"{side}_elbow"]
        ear = landmarks[f"{side}_ear"]

        body_angle = 180 - calculate_angle(
            sh.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )
        hip_sag = 180 - calculate_angle(
            sh.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )
        elbow_offset = abs(sh.x - elbow.x)
        neck_angle = calculate_angle(
            ear.to_tuple(), sh.to_tuple(), hip.to_tuple(),
        )

        return {
            "body_line_angle": round(body_angle, 1),
            "hip_sag": round(hip_sag, 1),
            "hip_sag_angle": round(hip_sag, 1),
            "hip_angle": round(hip_sag, 1),
            "elbow_offset": round(elbow_offset, 3),
            "neck_angle": round(neck_angle, 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        bl = features.get("body_line_angle", 0)
        hip = features.get("hip_sag_angle", features.get("hip_sag", 0))
        prev = state.get("phase", "ready")

        now = time.time()
        self.jitter_buffer.append({"bl": bl, "hip": hip, "t": now})

        if bl > 28 or hip > 35:
            self.hold_start = None
            return "collapsed" if prev in ("holding", "unstable") else "ready"

        if self.hold_start is None:
            self.hold_start = now
        self.total_hold = now - self.hold_start

        if len(self.jitter_buffer) >= 15:
            recent = list(self.jitter_buffer)[-15:]
            bl_mean = sum(d["bl"] for d in recent) / len(recent)
            bl_var = sum((d["bl"] - bl_mean) ** 2 for d in recent) / len(recent)
            if bl_var > 3.0:
                state["phase"] = "unstable"
                return "unstable"

        state["phase"] = "holding"
        return "holding"

    def score_frame(self, features: dict, phase: str) -> dict:
        if phase not in PLANK_STAGE_RULES:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}

        rules = PLANK_STAGE_RULES[phase]
        total_score = 0.0
        total_weight = 0.0
        detail_scores: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None and name == "hip_sag_angle":
                raw = features.get("hip_sag")
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

        if phase == "unstable":
            issues.append("身体晃动过大，核心控制不稳定")
            feedback.append("放慢呼吸，保持稳定支撑")

        if phase == "collapsed":
            issues.append("支撑姿态已崩溃，请重新调整")
            feedback.append("先回到标准平板姿势，再开始计时")

        if not issues and phase == "holding":
            feedback.append("姿态稳定，保持核心收紧与均匀呼吸")

        final = round(total_score / total_weight, 1) if total_weight else 0
        if phase == "ready":
            final = 0

        detail_scores["hold_duration"] = round(self.total_hold, 1)
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        if name == "body_line_angle":
            if value > 22:
                return "塌腰或撅臀明显，身体未保持直线"
            if value > 12:
                return "身体直线略有偏差"
            return "身体直线控制略差"

        if name == "hip_sag_angle":
            if value > 22:
                return "髋部明显下沉或抬高"
            if value > 14:
                return "髋部稳定性不足"
            return "髋部控制略差"

        if name == "elbow_offset":
            if value > 0.10:
                return "肩膀未在手肘正上方"
            return "肩肘对齐略有偏差"

        if name == "neck_angle":
            if value < 45:
                return "低头过多，颈部未保持中立"
            if value > 75:
                return "抬头过多，颈部紧张"
            return "颈部姿态略有偏差"

        return f"{name} 偏差较大"

    @staticmethod
    def _suggest_fix(name: str, phase: str, value: float) -> str:
        suggestions = {
            "body_line_angle": {
                "ready": "调整至肩-髋-踝成一直线后再开始支撑",
                "holding": "收紧核心，保持肩-髋-踝成一直线",
                "unstable": "缩小晃动幅度，稳定躯干",
                "collapsed": "重新进入标准平板姿势",
            },
            "hip_sag_angle": {
                "ready": "收紧腹部与臀部，稳定骨盆",
                "holding": "保持骨盆中立，避免髋部下沉",
                "unstable": "核心持续发力，控制髋部",
                "collapsed": "先恢复核心控制再继续",
            },
            "elbow_offset": {
                "ready": "手肘位于肩膀正下方",
                "holding": "让肩膀正对手肘，减少手肘外移",
                "unstable": "检查手肘位置是否偏移",
            },
            "neck_angle": {
                "ready": "目视下方，保持颈部中立",
                "holding": "保持颈部中立，避免抬头或低头过多",
            },
        }
        return suggestions.get(name, {}).get(phase, "")
