"""First-pass analyzers for gym strength exercises.

These analyzers intentionally use human pose landmarks only. Barbell,
dumbbell, and cable paths are approximated from wrist trajectories so they can
work with the current MediaPipe-only pipeline and template scoring.
"""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer,
    Keypoints,
    calculate_angle,
)


UPPER_REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_hip", "right_hip",
}

LOWER_REQUIRED = {
    "left_shoulder", "right_shoulder",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_wrist", "right_wrist",
}


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _side_angles(landmarks: Keypoints, joint: str) -> tuple[float, float]:
    if joint == "elbow":
        left = calculate_angle(
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_elbow"].to_tuple(),
            landmarks["left_wrist"].to_tuple(),
        )
        right = calculate_angle(
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_elbow"].to_tuple(),
            landmarks["right_wrist"].to_tuple(),
        )
        return left, right
    if joint == "shoulder":
        left = calculate_angle(
            landmarks["left_hip"].to_tuple(),
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_elbow"].to_tuple(),
        )
        right = calculate_angle(
            landmarks["right_hip"].to_tuple(),
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_elbow"].to_tuple(),
        )
        return left, right
    raise ValueError(f"Unsupported joint: {joint}")


def _trunk_angle(landmarks: Keypoints) -> float:
    hip_x = (landmarks["left_hip"].x + landmarks["right_hip"].x) / 2
    hip_y = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
    shoulder_x = (landmarks["left_shoulder"].x + landmarks["right_shoulder"].x) / 2
    shoulder_y = (landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2
    return calculate_angle((hip_x, hip_y - 0.1), (hip_x, hip_y), (shoulder_x, shoulder_y))


def _wrist_center(landmarks: Keypoints) -> tuple[float, float]:
    return (
        (landmarks["left_wrist"].x + landmarks["right_wrist"].x) / 2,
        (landmarks["left_wrist"].y + landmarks["right_wrist"].y) / 2,
    )


class UpperBodyRepAnalyzer(BaseExerciseAnalyzer):
    """Shared analyzer for press, fly, pull, and pulldown patterns."""

    exercise_type = "upper_body_strength"
    top_phase = "top"
    bottom_phase = "bottom"
    motion_metric = "elbow_angle"
    top_threshold = 155.0
    bottom_threshold = 105.0
    completion_phase = "bottom"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("moving", self.top_phase, self.bottom_phase)

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("moving", self.top_phase), (self.completion_phase,))

    def rep_summary_phase(self) -> str:
        return self.top_phase

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        metric = self.motion_metric
        if self.top_threshold >= self.bottom_threshold:
            peak = dict(max(samples, key=lambda sample: sample.get(metric, 0)))
        else:
            peak = dict(min(samples, key=lambda sample: sample.get(metric, 180)))
        peak["max_symmetry_diff"] = round(max((s.get("symmetry_diff", 0) for s in samples), default=0), 1)
        peak["max_trunk_angle"] = round(max((s.get("trunk_angle", 0) for s in samples), default=0), 1)
        return peak

    def detect_phase(self, features: dict, state: dict) -> str:
        metric = features.get(self.motion_metric, self.bottom_threshold)
        prev = state.get(f"prev_{self.motion_metric}", metric)
        delta = metric - prev
        state[f"prev_{self.motion_metric}"] = metric

        if self.top_threshold >= self.bottom_threshold:
            if metric >= self.top_threshold:
                return self.top_phase
            if metric <= self.bottom_threshold:
                return self.bottom_phase
            return "moving" if delta >= -2 else "moving"

        if metric <= self.top_threshold:
            return self.top_phase
        if metric >= self.bottom_threshold:
            return self.bottom_phase
        return "moving"

    def score_frame(self, features: dict, phase: str) -> dict:
        return self._score_common(features, phase)

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}
        return self._score_common(summary, self.top_phase)

    def _score_common(self, features: dict, phase: str) -> dict:
        rules = self._rules().get(phase) or self._rules().get(self.top_phase, {})
        total = 0.0
        weight = 0.0
        detail: dict[str, float] = {}
        issues: list[str] = []
        feedback: list[str] = []

        for name, rule in rules.items():
            raw = features.get(name)
            if raw is None:
                continue
            score = self._score_by_range(raw, rule["good_range"], rule["bad_range"])
            detail[name] = round(score, 1)
            total += score * rule["weight"]
            weight += rule["weight"]
            if score < 65:
                issues.append(rule["issue"])
                feedback.append(rule["feedback"])

        final = round(total / weight, 1) if weight else 0
        if not issues and phase in (self.top_phase, self.bottom_phase):
            feedback.append("动作幅度、稳定性和左右同步整体可控。")
        return {"score": final, "issues": issues, "detail_scores": detail, "feedback": list(dict.fromkeys(feedback))}

    def _rules(self) -> dict[str, dict]:
        raise NotImplementedError


class BenchPressAnalyzer(UpperBodyRepAnalyzer):
    exercise_type = "bench_press"
    top_phase = "top"
    bottom_phase = "bottom"
    motion_metric = "elbow_angle"
    top_threshold = 155.0
    bottom_threshold = 105.0
    completion_phase = "bottom"

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not UPPER_REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for bench press analysis")
        elbows = _side_angles(landmarks, "elbow")
        shoulders = _side_angles(landmarks, "shoulder")
        wrist_x, _ = _wrist_center(landmarks)
        elbow_center_x = (landmarks["left_elbow"].x + landmarks["right_elbow"].x) / 2
        return {
            "elbow_angle": round(_avg(list(elbows)), 1),
            "shoulder_angle": round(_avg(list(shoulders)), 1),
            "wrist_elbow_alignment": round(abs(wrist_x - elbow_center_x) * 100, 1),
            "symmetry_diff": round(abs(elbows[0] - elbows[1]), 1),
        }

    def _rules(self) -> dict[str, dict]:
        return {
            "top": {
                "elbow_angle": {"good_range": (155, 180), "bad_range": (130, 180), "weight": 0.38, "issue": "卧推推起幅度不足", "feedback": "推起到手臂接近伸直，但不要锁死肘关节。"},
                "wrist_elbow_alignment": {"good_range": (0, 9), "bad_range": (0, 18), "weight": 0.22, "issue": "手腕和肘部不在同一推举线上", "feedback": "保持手腕在肘部上方，避免手腕内扣或外漂。"},
                "symmetry_diff": {"good_range": (0, 16), "bad_range": (0, 32), "weight": 0.22, "issue": "左右推起不同步", "feedback": "两侧手臂同步推起，保持杠铃或哑铃轨迹平衡。"},
                "shoulder_angle": {"good_range": (45, 115), "bad_range": (25, 145), "weight": 0.18, "issue": "肩部角度偏离卧推轨迹", "feedback": "保持肩胛稳定，控制肘部在舒适角度下放。"},
            },
            "bottom": {
                "elbow_angle": {"good_range": (70, 115), "bad_range": (50, 135), "weight": 0.45, "issue": "卧推下放幅度异常", "feedback": "下放到肘部充分弯曲且胸肩稳定的位置。"},
                "symmetry_diff": {"good_range": (0, 16), "bad_range": (0, 32), "weight": 0.30, "issue": "底部左右不对称", "feedback": "底部停顿时两侧肘部高度和弯曲幅度保持一致。"},
                "wrist_elbow_alignment": {"good_range": (0, 9), "bad_range": (0, 18), "weight": 0.25, "issue": "底部手腕偏离肘部", "feedback": "下放时手腕保持中立，贴近肘部垂直线。"},
            },
        }


class DumbbellFlyAnalyzer(UpperBodyRepAnalyzer):
    exercise_type = "dumbbell_fly"
    top_phase = "closed"
    bottom_phase = "open"
    motion_metric = "wrist_path_width"
    top_threshold = 30.0
    bottom_threshold = 55.0
    completion_phase = "closed"

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not UPPER_REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for dumbbell fly analysis")
        elbows = _side_angles(landmarks, "elbow")
        shoulders = _side_angles(landmarks, "shoulder")
        wrist_width = abs(landmarks["left_wrist"].x - landmarks["right_wrist"].x) * 100
        shoulder_width = abs(landmarks["left_shoulder"].x - landmarks["right_shoulder"].x) * 100
        return {
            "shoulder_abduction_angle": round(_avg(list(shoulders)), 1),
            "elbow_bend_angle": round(_avg(list(elbows)), 1),
            "wrist_path_width": round(wrist_width, 1),
            "symmetry_diff": round(abs(elbows[0] - elbows[1]) + abs(wrist_width - shoulder_width) * 0.1, 1),
        }

    def _rules(self) -> dict[str, dict]:
        return {
            "open": {
                "wrist_path_width": {"good_range": (42, 75), "bad_range": (25, 90), "weight": 0.36, "issue": "飞鸟打开幅度不足或过大", "feedback": "双臂向两侧打开到胸部有拉伸感即可，避免过度下沉。"},
                "elbow_bend_angle": {"good_range": (125, 165), "bad_range": (95, 180), "weight": 0.28, "issue": "肘部弯曲保持不稳定", "feedback": "全程保持肘部微屈，不要变成卧推动作。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.22, "issue": "左右飞鸟轨迹不对称", "feedback": "两侧哑铃同步打开和合拢，保持轨迹一致。"},
                "shoulder_abduction_angle": {"good_range": (55, 125), "bad_range": (35, 150), "weight": 0.14, "issue": "肩部外展轨迹偏离", "feedback": "用胸部控制手臂弧线，肩部保持稳定。"},
            },
            "closed": {
                "wrist_path_width": {"good_range": (0, 38), "bad_range": (0, 60), "weight": 0.45, "issue": "飞鸟合拢不充分", "feedback": "顶部合拢到双手接近胸前上方，保持控制。"},
                "elbow_bend_angle": {"good_range": (125, 170), "bad_range": (95, 180), "weight": 0.30, "issue": "顶部肘部角度异常", "feedback": "顶部仍保持微屈，不要完全锁死。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.25, "issue": "顶部左右不同步", "feedback": "合拢时两侧同步回到中线。"},
            },
        }


class LatPulldownAnalyzer(UpperBodyRepAnalyzer):
    exercise_type = "lat_pulldown"
    top_phase = "bottom"
    bottom_phase = "top"
    motion_metric = "elbow_angle"
    top_threshold = 105.0
    bottom_threshold = 155.0
    completion_phase = "top"

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not UPPER_REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for lat pulldown analysis")
        elbows = _side_angles(landmarks, "elbow")
        shoulders = _side_angles(landmarks, "shoulder")
        wrist_y = (landmarks["left_wrist"].y + landmarks["right_wrist"].y) / 2
        shoulder_y = (landmarks["left_shoulder"].y + landmarks["right_shoulder"].y) / 2
        return {
            "elbow_angle": round(_avg(list(elbows)), 1),
            "shoulder_adduction_angle": round(_avg(list(shoulders)), 1),
            "wrist_height": round((wrist_y - shoulder_y) * 100, 1),
            "trunk_angle": round(_trunk_angle(landmarks), 1),
            "symmetry_diff": round(abs(elbows[0] - elbows[1]), 1),
        }

    def _rules(self) -> dict[str, dict]:
        return {
            "bottom": {
                "elbow_angle": {"good_range": (65, 110), "bad_range": (45, 135), "weight": 0.34, "issue": "高位下拉幅度不足", "feedback": "下拉到底部时肘部充分下沉，接近身体两侧。"},
                "trunk_angle": {"good_range": (0, 22), "bad_range": (0, 42), "weight": 0.22, "issue": "下拉时身体后仰过多", "feedback": "保持胸口微抬即可，不要用后仰借力。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.22, "issue": "左右下拉不同步", "feedback": "两侧肘部同步向下，保持肩胛控制。"},
                "wrist_height": {"good_range": (0, 32), "bad_range": (-20, 55), "weight": 0.22, "issue": "下拉终点位置异常", "feedback": "把手拉到上胸附近，不要只拉到头顶。"},
            },
            "top": {
                "elbow_angle": {"good_range": (150, 180), "bad_range": (125, 180), "weight": 0.45, "issue": "高位下拉回放不充分", "feedback": "回到顶部时让手臂充分伸展，保持肩胛稳定。"},
                "trunk_angle": {"good_range": (0, 20), "bad_range": (0, 40), "weight": 0.25, "issue": "顶部躯干不稳定", "feedback": "回放阶段控制身体不要晃动。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.30, "issue": "顶部左右不对称", "feedback": "顶部双臂伸展幅度保持一致。"},
            },
        }


class DumbbellShoulderPressAnalyzer(UpperBodyRepAnalyzer):
    exercise_type = "dumbbell_shoulder_press"
    top_phase = "top"
    bottom_phase = "rack"
    motion_metric = "elbow_angle"
    top_threshold = 155.0
    bottom_threshold = 105.0
    completion_phase = "rack"

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not UPPER_REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for dumbbell shoulder press analysis")
        elbows = _side_angles(landmarks, "elbow")
        shoulders = _side_angles(landmarks, "shoulder")
        wrist_x, _ = _wrist_center(landmarks)
        shoulder_x = (landmarks["left_shoulder"].x + landmarks["right_shoulder"].x) / 2
        return {
            "elbow_angle": round(_avg(list(elbows)), 1),
            "shoulder_angle": round(_avg(list(shoulders)), 1),
            "wrist_over_shoulder_offset": round(abs(wrist_x - shoulder_x) * 100, 1),
            "trunk_angle": round(_trunk_angle(landmarks), 1),
            "symmetry_diff": round(abs(elbows[0] - elbows[1]), 1),
        }

    def _rules(self) -> dict[str, dict]:
        return {
            "top": {
                "elbow_angle": {"good_range": (155, 180), "bad_range": (130, 180), "weight": 0.32, "issue": "哑铃推肩伸展不足", "feedback": "推到顶部时手臂接近伸直，避免耸肩代偿。"},
                "shoulder_angle": {"good_range": (145, 180), "bad_range": (110, 180), "weight": 0.24, "issue": "肩部上举幅度不足", "feedback": "让上臂充分上举到头顶附近。"},
                "wrist_over_shoulder_offset": {"good_range": (0, 14), "bad_range": (0, 28), "weight": 0.18, "issue": "顶部手腕偏离肩部中线", "feedback": "顶部保持哑铃在肩上方，不要前后漂移。"},
                "trunk_angle": {"good_range": (0, 20), "bad_range": (0, 40), "weight": 0.14, "issue": "推肩时躯干后仰", "feedback": "收紧核心，避免用腰背后仰借力。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.12, "issue": "左右推肩不同步", "feedback": "两侧哑铃同步上推和下放。"},
            },
            "rack": {
                "elbow_angle": {"good_range": (70, 115), "bad_range": (50, 135), "weight": 0.40, "issue": "底部回到架位不充分", "feedback": "下放到肘部弯曲、哑铃接近肩部的位置。"},
                "symmetry_diff": {"good_range": (0, 18), "bad_range": (0, 36), "weight": 0.30, "issue": "底部左右不对称", "feedback": "下放到底部时两侧保持同高。"},
                "trunk_angle": {"good_range": (0, 20), "bad_range": (0, 40), "weight": 0.30, "issue": "底部躯干不稳定", "feedback": "底部保持核心收紧，避免身体晃动。"},
            },
        }


class BarbellSquatAnalyzer(BaseExerciseAnalyzer):
    exercise_type = "barbell_squat"

    def rep_sample_phases(self) -> tuple[str, ...]:
        return ("descending", "bottom", "ascending")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        return (("descending", "bottom", "ascending"), ("standing",))

    def rep_summary_phase(self) -> str:
        return "bottom"

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        if not LOWER_REQUIRED.issubset(landmarks):
            raise ValueError("Missing keypoints for barbell squat analysis")
        left_knee = calculate_angle(
            landmarks["left_hip"].to_tuple(),
            landmarks["left_knee"].to_tuple(),
            landmarks["left_ankle"].to_tuple(),
        )
        right_knee = calculate_angle(
            landmarks["right_hip"].to_tuple(),
            landmarks["right_knee"].to_tuple(),
            landmarks["right_ankle"].to_tuple(),
        )
        left_hip = calculate_angle(
            landmarks["left_shoulder"].to_tuple(),
            landmarks["left_hip"].to_tuple(),
            landmarks["left_knee"].to_tuple(),
        )
        right_hip = calculate_angle(
            landmarks["right_shoulder"].to_tuple(),
            landmarks["right_hip"].to_tuple(),
            landmarks["right_knee"].to_tuple(),
        )
        wrist_x, _ = _wrist_center(landmarks)
        ankle_x = (landmarks["left_ankle"].x + landmarks["right_ankle"].x) / 2
        hip_y = (landmarks["left_hip"].y + landmarks["right_hip"].y) / 2
        knee_y = (landmarks["left_knee"].y + landmarks["right_knee"].y) / 2
        depth_ratio = round((hip_y - knee_y) * 100, 1)
        return {
            "knee_angle": round(_avg([left_knee, right_knee]), 1),
            "hip_angle": round(_avg([left_hip, right_hip]), 1),
            "trunk_angle": round(_trunk_angle(landmarks), 1),
            "depth_ratio": depth_ratio,
            "bar_path_offset": round(abs(wrist_x - ankle_x) * 100, 1),
            "knee_symmetry_diff": round(abs(left_knee - right_knee), 1),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        knee = features.get("knee_angle", 170)
        prev = state.get("prev_knee", knee)
        delta = knee - prev
        state["prev_knee"] = knee
        if knee > 150:
            return "standing"
        if knee < 115:
            return "bottom"
        if delta < -1.5:
            return "descending"
        if delta > 1.5:
            return "ascending"
        return "bottom"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        bottom = dict(min(samples, key=lambda sample: sample.get("knee_angle", 180)))
        bottom["max_bar_path_offset"] = round(max((s.get("bar_path_offset", 0) for s in samples), default=0), 1)
        bottom["max_trunk_angle"] = round(max((s.get("trunk_angle", 0) for s in samples), default=0), 1)
        return bottom

    def score_frame(self, features: dict, phase: str) -> dict:
        return self.score_rep(features)

    def score_rep(self, summary: dict[str, float]) -> dict:
        if not summary:
            return {"score": 0, "issues": [], "detail_scores": {}, "feedback": []}
        depth_score = self._score_by_range(summary.get("knee_angle", 180), (70, 115), (55, 135))
        trunk_score = self._score_by_range(summary.get("max_trunk_angle", summary.get("trunk_angle", 0)), (0, 35), (0, 55))
        path_score = self._score_by_range(summary.get("max_bar_path_offset", summary.get("bar_path_offset", 0)), (0, 14), (0, 28))
        symmetry_score = self._score_by_range(summary.get("knee_symmetry_diff", 0), (0, 16), (0, 35))
        issues: list[str] = []
        feedback: list[str] = []
        if depth_score < 65:
            issues.append("杠铃深蹲深度不足或过深")
            feedback.append("下蹲到大腿接近水平，并保持底部稳定。")
        if trunk_score < 65:
            issues.append("杠铃深蹲躯干前倾过大")
            feedback.append("收紧核心，保持胸口微抬，让杠铃路径更稳定。")
        if path_score < 65:
            issues.append("杠铃路径偏移明显")
            feedback.append("让手腕中点轨迹尽量靠近脚掌中线，避免重心前后漂移。")
        if symmetry_score < 65:
            issues.append("左右膝关节不对称")
            feedback.append("两侧膝盖同步向脚尖方向移动，保持重心居中。")
        if not issues:
            feedback.append("杠铃深蹲深度、躯干控制和路径稳定性整体可控。")
        score = round(depth_score * 0.36 + trunk_score * 0.24 + path_score * 0.20 + symmetry_score * 0.20, 1)
        return {
            "score": score,
            "issues": issues,
            "detail_scores": {
                "depth": round(depth_score, 1),
                "trunk": round(trunk_score, 1),
                "bar_path": round(path_score, 1),
                "symmetry": round(symmetry_score, 1),
            },
            "feedback": feedback,
        }
