from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.models import AnalysisResult, NormalizedKeypoint
import time
from collections import deque


Keypoints = dict[str, NormalizedKeypoint]
SQUAT_REQUIRED_KEYPOINTS = {
    "left_shoulder",
    "right_shoulder",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
}

# 分阶段标准角度配置
SQUAT_STAGE_RULES = {
    "standing": {
        "knee_angle": {
            "ideal": 170,
            "good_range": (155, 180),
            "bad_range": (130, 180),
            "weight": 0.30,
        },
        "hip_angle": {
            "ideal": 170,
            "good_range": (150, 180),
            "bad_range": (120, 180),
            "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 10,
            "good_range": (0, 20),
            "bad_range": (0, 40),
            "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0,
            "good_range": (0, 10),
            "bad_range": (0, 25),
            "weight": 0.20,
        },
    },
    "down": {
        "knee_angle": {
            "ideal": 120,
            "good_range": (90, 150),
            "bad_range": (70, 170),
            "weight": 0.35,
        },
        "hip_angle": {
            "ideal": 120,
            "good_range": (80, 150),
            "bad_range": (60, 170),
            "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20,
            "good_range": (5, 35),
            "bad_range": (0, 50),
            "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0,
            "good_range": (0, 12),
            "bad_range": (0, 30),
            "weight": 0.15,
        },
    },
    "bottom": {
        "knee_angle": {
            "ideal": 90,
            "good_range": (75, 110),
            "bad_range": (60, 130),
            "weight": 0.40,
        },
        "hip_angle": {
            "ideal": 90,
            "good_range": (70, 120),
            "bad_range": (50, 140),
            "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 20,
            "good_range": (5, 35),
            "bad_range": (0, 55),
            "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0,
            "good_range": (0, 10),
            "bad_range": (0, 25),
            "weight": 0.10,
        },
    },
    "up": {
        "knee_angle": {
            "ideal": 130,
            "good_range": (100, 160),
            "bad_range": (80, 175),
            "weight": 0.35,
        },
        "hip_angle": {
            "ideal": 130,
            "good_range": (90, 160),
            "bad_range": (70, 175),
            "weight": 0.25,
        },
        "trunk_angle": {
            "ideal": 15,
            "good_range": (0, 30),
            "bad_range": (0, 50),
            "weight": 0.25,
        },
        "knee_symmetry_diff": {
            "ideal": 0,
            "good_range": (0, 12),
            "bad_range": (0, 30),
            "weight": 0.15,
        },
    },
}


class ExerciseAnalyzer:
    def __init__(self, exercise: str):
        self.exercise = exercise
        self.stage = "ready"
        self.count = 0
        self.valid_count = 0
        self._last_down_was_valid = False
        self.start_time = time.time()
        self.scores_history = []
        
        # 用于平滑防抖的历史数据
        self.angle_history = deque(maxlen=5)  # 保存最近5帧角度数据
        self.previous_knee_angle = None
        self.previous_stage = "ready"
        self.stage_stability_counter = 0  # 阶段稳定性计数器

    def analyze(self, keypoints: Keypoints) -> AnalysisResult:
        lower_body_keypoints = {
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
            "left_ankle",
            "right_ankle",
        }
        missing_shoulders = "left_shoulder" not in keypoints or "right_shoulder" not in keypoints
        if self.exercise == "squat" and missing_shoulders and lower_body_keypoints.issubset(keypoints):
            return self._analyze_squat_lower_body_compat(keypoints)

        if self.exercise == "squat" and not SQUAT_REQUIRED_KEYPOINTS.issubset(keypoints):
            return AnalysisResult(
                exercise=self.exercise,
                stage="invalid",
                count=self.count,
                valid_count=self.valid_count,
                score=0,
                errors=["关键点不足"],
            )
        if self.exercise == "squat":
            return self._analyze_squat(keypoints)
        return AnalysisResult(
            exercise=self.exercise,
            stage="unsupported",
            score=0,
            errors=[f"暂不支持动作: {self.exercise}"],
        )

    def _analyze_squat_lower_body_compat(self, keypoints: Keypoints) -> AnalysisResult:
        hip_y = (keypoints["left_hip"].y + keypoints["right_hip"].y) / 2
        knee_y = (keypoints["left_knee"].y + keypoints["right_knee"].y) / 2
        hip_above_knee = knee_y - hip_y

        if hip_above_knee >= 0.3:
            current_stage = "up"
            score = 92
            errors = []
        elif hip_above_knee >= 0.12:
            current_stage = "bottom"
            score = 72
            errors = ["下蹲深度不足"]
        else:
            current_stage = "bottom"
            score = 90
            errors = []

        if self.stage == "bottom" and current_stage == "up":
            self.count += 1
            if self._last_down_was_valid:
                self.valid_count += 1
            self.scores_history.append(score)

        if current_stage == "bottom":
            self._last_down_was_valid = len(errors) == 0

        self.previous_stage = self.stage
        self.stage = current_stage

        return AnalysisResult(
            exercise=self.exercise,
            stage=current_stage,
            count=self.count,
            valid_count=self.valid_count,
            score=score,
            errors=errors,
            features={"hip_knee_offset": round(hip_above_knee, 3)},
        )

    def _analyze_squat(self, keypoints: Keypoints) -> AnalysisResult:
        # 计算四个角度指标
        knee_angle, knee_symmetry_diff = self._calculate_knee_angles(keypoints)
        hip_angle = self._calculate_hip_angle(keypoints)
        trunk_angle = self._calculate_trunk_angle(keypoints)

        # 保存到历史记录用于平滑防抖
        self.angle_history.append({
            "knee_angle": knee_angle,
            "hip_angle": hip_angle,
            "trunk_angle": trunk_angle,
            "knee_symmetry_diff": knee_symmetry_diff,
            "timestamp": time.time()
        })

        # 使用平滑后的角度
        smoothed_angles = self._smooth_angles()
        smoothed_knee_angle = smoothed_angles["knee_angle"]

        # 识别当前动作阶段
        current_stage = self._detect_squat_stage(smoothed_knee_angle)

        # 阶段稳定性检测（防抖）
        current_stage = self._apply_stage_stability(current_stage)

        # 计算评分
        angles = {
            "knee_angle": smoothed_angles["knee_angle"],
            "hip_angle": smoothed_angles["hip_angle"],
            "trunk_angle": smoothed_angles["trunk_angle"],
            "knee_symmetry_diff": smoothed_angles["knee_symmetry_diff"],
        }
        score, detail_scores = self._calculate_realtime_score(current_stage, angles)

        # 生成反馈
        errors = self._generate_feedback(current_stage, detail_scores, angles)

        # 动作完成时记录分数
        if self.stage == "bottom" and current_stage == "up":
            self.count += 1
            if self._last_down_was_valid:
                self.valid_count += 1
            self.scores_history.append(score)

        # 在下蹲最低点判断动作是否有效
        if current_stage == "bottom":
            self._last_down_was_valid = len(errors) == 0

        # 更新状态
        self.previous_knee_angle = smoothed_knee_angle
        self.previous_stage = self.stage
        self.stage = current_stage

        return AnalysisResult(
            exercise=self.exercise,
            stage=current_stage,
            count=self.count,
            valid_count=self.valid_count,
            score=score,
            errors=errors,
            features={
                "knee_angle": round(smoothed_angles["knee_angle"], 1),
                "hip_angle": round(smoothed_angles["hip_angle"], 1),
                "trunk_angle": round(smoothed_angles["trunk_angle"], 1),
                "knee_symmetry_diff": round(smoothed_angles["knee_symmetry_diff"], 1),
                "detail_scores": detail_scores,
            },
        )

    def _smooth_angles(self):
        """对角度数据进行滑动平均平滑处理"""
        if len(self.angle_history) == 0:
            return {
                "knee_angle": 170,
                "hip_angle": 170,
                "trunk_angle": 10,
                "knee_symmetry_diff": 0,
            }

        result = {}
        metrics = ["knee_angle", "hip_angle", "trunk_angle", "knee_symmetry_diff"]
        
        for metric in metrics:
            values = [h[metric] for h in self.angle_history]
            result[metric] = sum(values) / len(values)

        return result

    def _detect_squat_stage(self, current_knee_angle):
        """根据膝关节角度和变化趋势判断深蹲阶段"""
        if self.previous_knee_angle is None:
            self.previous_knee_angle = current_knee_angle
            return "standing"

        delta = current_knee_angle - self.previous_knee_angle

        # 站立阶段：膝角较大
        if current_knee_angle > 155:
            return "standing"

        # 最低点阶段：膝角较小且变化不大
        if 70 <= current_knee_angle <= 110 and abs(delta) <= 3:
            return "bottom"

        # 下降阶段：膝角变小
        if delta < -2:
            return "down"

        # 起身阶段：膝角变大
        if delta > 2:
            return "up"

        # 默认返回下降阶段
        return "down"

    def _apply_stage_stability(self, current_stage):
        """阶段稳定性检测，防止频繁切换"""
        if current_stage == self.stage:
            self.stage_stability_counter = 0
            return current_stage

        # 阶段变化需要连续3帧稳定
        self.stage_stability_counter += 1
        if self.stage_stability_counter >= 3:
            self.stage_stability_counter = 0
            return current_stage

        # 未稳定，保持原阶段
        return self.stage

    @staticmethod
    def _score_by_range(value, good_range, bad_range):
        """
        连续评分函数
        value: 当前角度
        good_range: 标准范围，落在这里接近满分
        bad_range: 可接受范围，超出后得分较低
        """
        good_min, good_max = good_range
        bad_min, bad_max = bad_range

        # 最优范围内，满分
        if good_min <= value <= good_max:
            return 100

        # 完全超出可接受范围，低分
        if value < bad_min or value > bad_max:
            return 40

        # 低于标准范围，但还在可接受范围
        if bad_min <= value < good_min:
            ratio = (value - bad_min) / (good_min - bad_min)
            return 40 + ratio * 60

        # 高于标准范围，但还在可接受范围
        if good_max < value <= bad_max:
            ratio = (bad_max - value) / (bad_max - good_max)
            return 40 + ratio * 60

        return 40

    def _calculate_realtime_score(self, stage, angles):
        """
        计算实时总分
        stage: 当前动作阶段
        angles: 当前帧计算出的角度字典
        """
        if stage not in SQUAT_STAGE_RULES:
            return 0, {}

        rules = SQUAT_STAGE_RULES[stage]

        total_score = 0
        total_weight = 0
        detail_scores = {}

        for name, rule in rules.items():
            if name not in angles:
                continue

            value = angles[name]

            score = self._score_by_range(
                value=value,
                good_range=rule["good_range"],
                bad_range=rule["bad_range"]
            )

            weight = rule["weight"]

            detail_scores[name] = {
                "value": round(value, 1),
                "score": round(score, 1),
                "weight": weight,
                "ideal": rule["ideal"],
                "good_range": rule["good_range"],
            }

            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0, detail_scores

        final_score = total_score / total_weight

        return round(final_score, 1), detail_scores

    def _generate_feedback(self, stage, detail_scores, angles):
        """根据阶段和评分生成实时反馈"""
        feedback = []

        for name, item in detail_scores.items():
            score = item["score"]
            value = item["value"]

            if score >= 85:
                continue

            if name == "knee_angle":
                if stage == "bottom" and value > 110:
                    feedback.append("下蹲深度不足，建议继续降低重心")
                elif stage == "bottom" and value < 75:
                    feedback.append("膝关节弯曲过度，注意控制动作幅度")
                elif stage == "standing" and value < 155:
                    feedback.append("站立时膝关节未完全伸直")
                elif stage == "down" and value < 90:
                    feedback.append("下蹲速度过快，建议放慢动作")

            elif name == "hip_angle":
                if stage == "bottom" and value > 120:
                    feedback.append("臀部后坐不足，深蹲深度不够")
                elif stage == "standing" and value < 150:
                    feedback.append("站立时髋关节未完全伸直")

            elif name == "trunk_angle":
                if value > 35:
                    feedback.append("躯干前倾过大，注意保持背部挺直")
                elif stage == "standing" and value > 20:
                    feedback.append("站立时身体应保持正直")

            elif name == "knee_symmetry_diff":
                if value > 10:
                    feedback.append("左右膝关节角度不一致，注意保持平衡")
                elif value > 15:
                    feedback.append("左右腿发力不均，请调整站姿")

        return feedback

    @staticmethod
    def _calculate_knee_angles(keypoints):
        """计算膝关节角度和对称性差异"""
        left_knee_angle = calculate_angle(
            keypoints["left_hip"].to_tuple(),
            keypoints["left_knee"].to_tuple(),
            keypoints["left_ankle"].to_tuple(),
        )
        right_knee_angle = calculate_angle(
            keypoints["right_hip"].to_tuple(),
            keypoints["right_knee"].to_tuple(),
            keypoints["right_ankle"].to_tuple(),
        )
        
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        symmetry_diff = abs(left_knee_angle - right_knee_angle)
        
        return avg_knee_angle, symmetry_diff

    @staticmethod
    def _calculate_hip_angle(keypoints):
        """计算髋关节角度（肩-髋-膝）"""
        left_hip_angle = calculate_angle(
            keypoints["left_shoulder"].to_tuple(),
            keypoints["left_hip"].to_tuple(),
            keypoints["left_knee"].to_tuple(),
        )
        right_hip_angle = calculate_angle(
            keypoints["right_shoulder"].to_tuple(),
            keypoints["right_hip"].to_tuple(),
            keypoints["right_knee"].to_tuple(),
        )
        
        return (left_hip_angle + right_hip_angle) / 2

    @staticmethod
    def _calculate_trunk_angle(keypoints):
        """计算躯干角度（肩-髋-垂直线）"""
        hip_center_x = (keypoints["left_hip"].x + keypoints["right_hip"].x) / 2
        hip_center_y = (keypoints["left_hip"].y + keypoints["right_hip"].y) / 2
        shoulder_center_x = (keypoints["left_shoulder"].x + keypoints["right_shoulder"].x) / 2
        shoulder_center_y = (keypoints["left_shoulder"].y + keypoints["right_shoulder"].y) / 2

        # 躯干角度：肩-髋连线与垂直线的夹角
        return calculate_angle(
            (hip_center_x, hip_center_y - 0.1),  # 髋部上方的点（垂直方向）
            (hip_center_x, hip_center_y),
            (shoulder_center_x, shoulder_center_y)
        )

    def get_session_summary(self):
        duration_seconds = int(time.time() - self.start_time)
        error_count = self.count - self.valid_count
        average_score = int(sum(self.scores_history) / len(self.scores_history)) if self.scores_history else 0
        
        return {
            "exercise": self.exercise,
            "duration_seconds": duration_seconds,
            "total_count": self.count,
            "valid_count": self.valid_count,
            "error_count": error_count,
            "average_score": average_score,
        }
