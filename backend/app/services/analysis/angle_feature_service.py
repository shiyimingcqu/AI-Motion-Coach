from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.models import NormalizedKeypoint
from typing import TypedDict


class SquatMetrics(TypedDict):
    knee_angle: float
    hip_angle: float
    trunk_angle: float
    knee_symmetry_diff: float


def extract_squat_features(keypoints: dict[str, NormalizedKeypoint]) -> SquatMetrics:
    """
    从 MediaPipe 关键点提取深蹲的角度特征

    Args:
        keypoints: MediaPipe 关键点字典

    Returns:
        SquatMetrics: 包含四项角度指标的字典

    Raises:
        ValueError: 当缺少必要关键点时
    """
    required_keypoints = [
        "left_shoulder", "right_shoulder",
        "left_hip", "right_hip",
        "left_knee", "right_knee",
        "left_ankle", "right_ankle"
    ]

    missing_keypoints = [kp for kp in required_keypoints if kp not in keypoints]
    if missing_keypoints:
        raise ValueError(f"缺少关键点: {', '.join(missing_keypoints)}")

    # 提取关键点坐标
    left_shoulder = keypoints["left_shoulder"]
    right_shoulder = keypoints["right_shoulder"]
    left_hip = keypoints["left_hip"]
    right_hip = keypoints["right_hip"]
    left_knee = keypoints["left_knee"]
    right_knee = keypoints["right_knee"]
    left_ankle = keypoints["left_ankle"]
    right_ankle = keypoints["right_ankle"]

    # 计算膝关节角度（髋-膝-踝）
    left_knee_angle = calculate_angle(
        (left_hip.x, left_hip.y),
        (left_knee.x, left_knee.y),
        (left_ankle.x, left_ankle.y)
    )
    right_knee_angle = calculate_angle(
        (right_hip.x, right_hip.y),
        (right_knee.x, right_knee.y),
        (right_ankle.x, right_ankle.y)
    )
    knee_angle = (left_knee_angle + right_knee_angle) / 2

    # 计算髋关节角度（肩-髋-膝）
    left_hip_angle = calculate_angle(
        (left_shoulder.x, left_shoulder.y),
        (left_hip.x, left_hip.y),
        (left_knee.x, left_knee.y)
    )
    right_hip_angle = calculate_angle(
        (right_shoulder.x, right_shoulder.y),
        (right_hip.x, right_hip.y),
        (right_knee.x, right_knee.y)
    )
    hip_angle = (left_hip_angle + right_hip_angle) / 2

    # 计算躯干角度（肩-髋-垂直线）
    # 使用髋部中心点和肩部中心点
    hip_center_x = (left_hip.x + right_hip.x) / 2
    hip_center_y = (left_hip.y + right_hip.y) / 2
    shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
    shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2

    # 躯干角度：肩-髋连线与垂直线的夹角
    # 使用髋部上方的一个点作为垂直线参考
    trunk_angle = calculate_angle(
        (hip_center_x, hip_center_y - 0.1),  # 髋部上方的点（垂直方向）
        (hip_center_x, hip_center_y),
        (shoulder_center_x, shoulder_center_y)
    )

    # 计算左右膝关节对称性差异
    knee_symmetry_diff = abs(left_knee_angle - right_knee_angle)

    return {
        "knee_angle": round(knee_angle, 1),
        "hip_angle": round(hip_angle, 1),
        "trunk_angle": round(trunk_angle, 1),
        "knee_symmetry_diff": round(knee_symmetry_diff, 1)
    }