"""Push-up analyzer — side-view, tracks elbow/body-line angles and phase."""

from app.services.analysis.analyzers.base_analyzer import (
    BaseExerciseAnalyzer, Keypoints, calculate_angle,
)


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

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        missing = REQUIRED - set(landmarks)
        if missing:
            raise ValueError(f"Missing keypoints: {missing}")

        # Use the side with higher-visibility landmarks
        left_vis = landmarks["left_shoulder"].visibility
        right_vis = landmarks["right_shoulder"].visibility
        side = "left" if left_vis >= right_vis else "right"

        shoulder = landmarks[f"{side}_shoulder"]
        elbow = landmarks[f"{side}_elbow"]
        wrist = landmarks[f"{side}_wrist"]
        hip = landmarks[f"{side}_hip"]
        knee = landmarks[f"{side}_knee"]
        ankle = landmarks[f"{side}_ankle"]

        # 1) elbow angle (shoulder → elbow → wrist)
        elbow_angle = calculate_angle(
            shoulder.to_tuple(), elbow.to_tuple(), wrist.to_tuple(),
        )
        # 2) shoulder angle (hip → shoulder → elbow)
        shoulder_angle = calculate_angle(
            hip.to_tuple(), shoulder.to_tuple(), elbow.to_tuple(),
        )
        # 3) body-line angle (shoulder → hip → ankle)
        body_line_angle = calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), ankle.to_tuple(),
        )
        # 4) hip sag angle (shoulder → hip → knee) — detects piking/butt-up
        hip_sag = 180 - calculate_angle(
            shoulder.to_tuple(), hip.to_tuple(), knee.to_tuple(),
        )

        # Symmetry: compare left/right shoulder heights and elbow angles
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
            "body_line_angle": round(180 - body_line_angle, 1),  # deviation from straight
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
            # near bottom, small movement
            return "bottom"
        return "top_support"

    def score_frame(self, features: dict, phase: str) -> dict:
        issues: list[str] = []
        detail_scores: dict[str, float] = {}
        total = 0.0
        count = 0

        # --- Movement range (40%) ---
        if phase in ("bottom",):
            # elbow should be ~90° at bottom
            elb = features.get("elbow_angle", 0)
            s = self._score_by_range(elb, (80, 100), (60, 130))
            detail_scores["range"] = round(s, 1)
            total += s * 0.4
            count += 0.4
            if s < 60:
                issues.append("肘关节弯曲不足，下降幅度不够")
            elif s < 80:
                issues.append("下降幅度略不足")

        # --- Body line (30%) ---
        bl = features.get("body_line_angle", 0)
        s_bl = self._score_by_range(bl, (0, 10), (0, 25))
        detail_scores["body_line"] = round(s_bl, 1)
        total += s_bl * 0.3
        count += 0.3
        if s_bl < 60:
            issues.append("身体未保持直线（塌腰或撅臀）")
        elif s_bl < 80:
            issues.append("身体直线略有偏差")

        # --- Symmetry (20%) ---
        sym = features.get("symmetry_diff", 0)
        s_sym = self._score_by_range(sym, (0, 8), (0, 20))
        detail_scores["symmetry"] = round(s_sym, 1)
        total += s_sym * 0.2
        count += 0.2
        if s_sym < 60:
            issues.append("左右发力不均，身体不对称")
        elif s_sym < 80:
            issues.append("左右略有不对称")

        # --- Stability / tempo (10%) ---
        hip = features.get("hip_sag", 0)
        s_hip = self._score_by_range(hip, (0, 8), (0, 20))
        detail_scores["stability"] = round(s_hip, 1)
        total += s_hip * 0.1
        count += 0.1

        score = round(total / count, 1) if count else 80.0
        return {"score": score, "issues": issues, "detail_scores": detail_scores, "feedback": []}
