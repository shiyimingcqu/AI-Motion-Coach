from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.models import AnalysisResult, NormalizedKeypoint


Keypoints = dict[str, NormalizedKeypoint]


class ExerciseAnalyzer:
    def __init__(self, exercise: str):
        self.exercise = exercise
        self.stage = "ready"
        self.count = 0
        self.valid_count = 0
        self._last_down_was_valid = False

    def analyze(self, keypoints: Keypoints) -> AnalysisResult:
        if self.exercise == "squat":
            return self._analyze_squat(keypoints)
        return AnalysisResult(
            exercise=self.exercise,
            stage="unsupported",
            score=0,
            errors=[f"暂不支持动作: {self.exercise}"],
        )

    def _analyze_squat(self, keypoints: Keypoints) -> AnalysisResult:
        hip_y = self._average_y(keypoints, "left_hip", "right_hip")
        knee_y = self._average_y(keypoints, "left_knee", "right_knee")
        ankle_y = self._average_y(keypoints, "left_ankle", "right_ankle")
        depth_ratio = (hip_y - knee_y) / max(ankle_y - knee_y, 0.01)
        knee_angle = self._average_knee_angle(keypoints)

        errors: list[str] = []
        score = 100

        if depth_ratio < -1.2:
            current_stage = "up"
        elif depth_ratio >= 0.15:
            current_stage = "down"
        else:
            current_stage = "transition"
            errors.append("下蹲深度不足")
            score -= 20

        if knee_angle < 15:
            errors.append("膝关节角度过小")
            score -= 10

        if self.stage == "down" and current_stage == "up":
            self.count += 1
            if self._last_down_was_valid:
                self.valid_count += 1

        if current_stage == "down":
            self._last_down_was_valid = not errors

        self.stage = current_stage
        return AnalysisResult(
            exercise=self.exercise,
            stage=current_stage,
            count=self.count,
            valid_count=self.valid_count,
            score=max(score, 0),
            errors=errors,
            features={
                "depth_ratio": round(depth_ratio, 4),
                "knee_angle": round(knee_angle, 2),
            },
        )

    @staticmethod
    def _average_y(keypoints: Keypoints, first: str, second: str) -> float:
        return (keypoints[first].y + keypoints[second].y) / 2

    @staticmethod
    def _average_knee_angle(keypoints: Keypoints) -> float:
        left = calculate_angle(
            keypoints["left_hip"].to_tuple(),
            keypoints["left_knee"].to_tuple(),
            keypoints["left_ankle"].to_tuple(),
        )
        right = calculate_angle(
            keypoints["right_hip"].to_tuple(),
            keypoints["right_knee"].to_tuple(),
            keypoints["right_ankle"].to_tuple(),
        )
        return (left + right) / 2
