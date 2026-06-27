"""Squat analyzer — stage detection, angle computation, and per-frame scoring."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


SQUAT_STAGE_RULES = {
    "standing": {
        "knee_angle": {
            "ideal": 170, "good_range": (155, 180), "bad_range": (130, 180), "weight": 0.30,
        },
        "hip_angle": {
            "ideal": 170, "good_range": (150, 180), "bad_range": (120, 180), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 10, "good_range": (0, 20), "bad_range": (0, 40), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 25), "weight": 0.20,
        },
    },
    "down": {
        "knee_angle": {
            "ideal": 120, "good_range": (90, 150), "bad_range": (70, 170), "weight": 0.35,
        },
        "hip_angle": {
            "ideal": 120, "good_range": (80, 150), "bad_range": (60, 170), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20, "good_range": (5, 35), "bad_range": (0, 50), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 12), "bad_range": (0, 30), "weight": 0.15,
        },
    },
    "bottom": {
        "knee_angle": {
            "ideal": 90, "good_range": (75, 110), "bad_range": (60, 130), "weight": 0.40,
        },
        "hip_angle": {
            "ideal": 90, "good_range": (70, 120), "bad_range": (50, 140), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20, "good_range": (5, 35), "bad_range": (0, 55), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 10), "bad_range": (0, 25), "weight": 0.10,
        },
    },
    "up": {
        "knee_angle": {
            "ideal": 130, "good_range": (100, 160), "bad_range": (80, 175), "weight": 0.35,
        },
        "hip_angle": {
            "ideal": 130, "good_range": (90, 160), "bad_range": (70, 175), "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 15, "good_range": (0, 30), "bad_range": (0, 50), "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0, "good_range": (0, 12), "bad_range": (0, 30), "weight": 0.15,
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

        if knee > 155:
            return "standing"
        if 70 <= knee <= 110 and abs(delta) <= 3:
            return "bottom"
        if delta < -2:
            return "down"
        if delta > 2:
            return "up"
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
            if s < 75:
                issues.append(self._describe_issue(name, phase, raw))

        final = round(total_score / total_weight, 1) if total_weight else 0
        return {"score": final, "issues": issues, "detail_scores": detail_scores, "feedback": feedback}

    @staticmethod
    def _describe_issue(name: str, phase: str, value: float) -> str:
        descriptions = {
            "knee_angle": {
                "standing": "站立时膝关节未完全伸直",
                "down": "下蹲速度过快" if value < 90 else "膝关节弯曲角度不佳",
                "bottom": "下蹲深度不足" if value > 110 else "膝关节过度弯曲",
                "up": "起身时膝关节角度异常",
            },
            "hip_angle": {
                "standing": "站立时髋关节未完全伸直",
                "down": "臀部后坐不足",
                "bottom": "深蹲深度不够",
                "up": "起身时髋关节角度异常",
            },
            "trunk_angle": {
                "standing": "身体应保持正直",
                "down": "躯干前倾过大",
                "bottom": "躯干前倾过大",
                "up": "起身时躯干前倾",
            },
            "knee_symmetry_diff": {
                "standing": "站姿左右不平衡",
                "down": "左右膝关节不一致",
                "bottom": "左右发力不均",
                "up": "起身时左右不平衡",
            },
        }
        return descriptions.get(name, {}).get(phase, f"{name} 偏差较大")
