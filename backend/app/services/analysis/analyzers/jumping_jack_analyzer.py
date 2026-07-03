"""Jumping-jack analyzer - front-view, tracks arm/leg spread and synchrony."""

import math

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer,
    Keypoints,
    calculate_angle,
)


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

    def _should_count_rep(self, current_stage: str, phase: str) -> bool:
        return (
            current_stage in ("open_peak", "closing", "opening")
            and phase in ("complete", "closed")
        ) or (current_stage == "complete" and phase == "closed")

    def _mark_rep_checkpoint(self, phase: str, score_result: dict) -> None:
        if phase in ("open_peak", "opening"):
            self._last_down_was_valid = len(score_result["issues"]) == 0

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

        return {
            "ankle_distance": round(foot_distance, 4),
            "foot_distance": round(foot_distance, 4),
            "spread_ratio": round(spread_ratio, 3),
            "leg_spread_angle": round(leg_spread_angle, 1),
            "wrist_height": round(wrist_height, 4),
            "avg_arm_height": round(wrist_height, 4),
            "arm_height_diff": round(arm_height_diff, 4),
            "avg_arm_angle": round((left_arm_angle + right_arm_angle) / 2, 1),
            "shoulder_abduction_angle": round((left_shoulder_abduction + right_shoulder_abduction) / 2, 1),
            "arm_angle_diff": round(arm_angle_diff, 1),
            "left_arm_height": round(left_arm_height, 4),
            "right_arm_height": round(right_arm_height, 4),
        }

    def detect_phase(self, features: dict, state: dict) -> str:
        foot = features.get("foot_distance", 0)
        arm_h = features.get("avg_arm_height", 0)

        prev_phase = self.stage if self.stage not in ("ready", "") else "closed"
        state["phase"] = prev_phase

        if foot < 0.15 and arm_h < 0.05:
            return "closed"
        if prev_phase == "closed" and (foot >= 0.15 or arm_h >= 0.05):
            state["opening_foot"] = foot
            return "opening"
        if foot >= 0.25 and arm_h >= 0.15:
            return "open_peak"
        if prev_phase in ("open_peak", "opening") and foot < 0.2:
            return "closing"
        if prev_phase in ("closing",) and foot < 0.15 and arm_h < 0.05:
            return "complete"

        return prev_phase

    def score_frame(self, features: dict, phase: str) -> dict:
        issues: list[str] = []
        detail_scores: dict[str, float] = {}
        total = 0.0
        count = 0.0

        ah = features.get("avg_arm_height", 0)
        s_arm = self._score_by_range(ah, (0.15, 0.40), (0.0, 0.50))
        detail_scores["arm_range"] = round(s_arm, 1)
        total += s_arm * 0.25
        count += 0.25
        if s_arm < 60:
            issues.append("手臂未充分举过头顶")
        elif s_arm < 80:
            issues.append("手臂举高幅度略不足")

        sp = features.get("spread_ratio", 0)
        s_leg = self._score_by_range(sp, (2.0, 5.0), (0.5, 6.0))
        detail_scores["leg_range"] = round(s_leg, 1)
        total += s_leg * 0.25
        count += 0.25
        if s_leg < 60:
            issues.append("双脚打开幅度不足")
        elif s_leg < 80:
            issues.append("腿部展开略不足")

        arm_h = features.get("avg_arm_height", 0)
        foot = features.get("foot_distance", 0)
        sync = 100 - min(100, abs(arm_h * 200 - foot * 400))
        detail_scores["synchrony"] = round(sync, 1)
        total += sync * 0.25
        count += 0.25
        if sync < 60:
            issues.append("手脚不同步，动作不协调")
        elif sync < 80:
            issues.append("手脚配合略有延迟")

        sym = features.get("arm_angle_diff", 0)
        s_sym = self._score_by_range(sym, (0, 15), (0, 40))
        detail_scores["symmetry"] = round(s_sym, 1)
        total += s_sym * 0.15
        count += 0.15
        if s_sym < 60:
            issues.append("左右动作不对称")

        detail_scores["rhythm"] = 85.0
        total += 85.0 * 0.10
        count += 0.10

        score = round(total / count, 1) if count else 80.0
        return {"score": score, "issues": issues, "detail_scores": detail_scores, "feedback": []}
