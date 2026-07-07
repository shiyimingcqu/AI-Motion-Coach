from dataclasses import asdict, dataclass

from app.services.analysis.exercise_metrics import (
    get_core_angle_labels,
    get_core_feature_keys,
)


@dataclass(frozen=True)
class ExerciseDefinition:
    key: str
    name: str
    description: str
    supported_metrics: list[str]
    core_angles: list[str]
    core_feature_keys: list[str]

    def to_dict(self):
        return asdict(self)


EXERCISES = [
    ExerciseDefinition(
        key="squat",
        name="深蹲",
        description="评估下蹲深度、膝髋协同、躯干控制和左右稳定性。",
        supported_metrics=["count", "valid_count", "score", "depth_ratio"],
        core_angles=get_core_angle_labels("squat"),
        core_feature_keys=get_core_feature_keys("squat"),
    ),
    ExerciseDefinition(
        key="push_up",
        name="俯卧撑",
        description="评估肘部屈伸幅度、肩部控制、身体直线和髋部稳定。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("push_up"),
        core_feature_keys=get_core_feature_keys("push_up"),
    ),
    ExerciseDefinition(
        key="plank",
        name="平板支撑",
        description="评估肩髋踝连线、髋部姿态、颈部角度和保持稳定性。",
        supported_metrics=["duration", "score", "error_count"],
        core_angles=get_core_angle_labels("plank"),
        core_feature_keys=get_core_feature_keys("plank"),
    ),
    ExerciseDefinition(
        key="jumping_jack",
        name="开合跳",
        description="评估肩外展、双腿打开幅度、手腕高度和脚踝间距。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("jumping_jack"),
        core_feature_keys=get_core_feature_keys("jumping_jack"),
    ),
    ExerciseDefinition(
        key="lunge", name="弓步蹲", description="评估膝关节角度、髋部控制和躯干稳定性。",
        supported_metrics=["count","valid_count","score"],
        core_angles=get_core_angle_labels("lunge"), core_feature_keys=get_core_feature_keys("lunge"),
    ),
    ExerciseDefinition(
        key="glute_bridge", name="臀桥", description="评估髋部伸展幅度和身体直线。",
        supported_metrics=["count","valid_count","score"],
        core_angles=get_core_angle_labels("glute_bridge"), core_feature_keys=get_core_feature_keys("glute_bridge"),
    ),
    ExerciseDefinition(
        key="high_knees", name="高抬腿", description="评估抬膝高度和节奏。",
        supported_metrics=["count","valid_count","score"],
        core_angles=get_core_angle_labels("high_knees"), core_feature_keys=get_core_feature_keys("high_knees"),
    ),
    ExerciseDefinition(
        key="burpee", name="波比跳", description="评估髋肩角度和身体控制。",
        supported_metrics=["count","valid_count","score"],
        core_angles=get_core_angle_labels("burpee"), core_feature_keys=get_core_feature_keys("burpee"),
    ),
    ExerciseDefinition(
        key="mountain_climber", name="登山跑", description="评估平板姿势、提膝高度和核心稳定。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("mountain_climber"),
        core_feature_keys=get_core_feature_keys("mountain_climber"),
    ),
    ExerciseDefinition(
        key="pull_up", name="引体向上", description="评估上拉幅度、身体控制和左右对称。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("pull_up"),
        core_feature_keys=get_core_feature_keys("pull_up"),
    ),
    ExerciseDefinition(
        key="bench_press", name="卧推", description="评估推起幅度、腕肘对齐、肩部轨迹和左右同步。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("bench_press"),
        core_feature_keys=get_core_feature_keys("bench_press"),
    ),
    ExerciseDefinition(
        key="barbell_squat", name="杠铃深蹲", description="评估下蹲深度、躯干控制、手腕近似杠铃路径和左右膝稳定。",
        supported_metrics=["count", "valid_count", "score", "depth_ratio"],
        core_angles=get_core_angle_labels("barbell_squat"),
        core_feature_keys=get_core_feature_keys("barbell_squat"),
    ),
    ExerciseDefinition(
        key="dumbbell_fly", name="哑铃飞鸟", description="评估飞鸟打开幅度、肘部微屈保持和左右轨迹对称。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("dumbbell_fly"),
        core_feature_keys=get_core_feature_keys("dumbbell_fly"),
    ),
    ExerciseDefinition(
        key="lat_pulldown", name="高位下拉", description="评估下拉幅度、手腕高度、躯干后仰和左右同步。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("lat_pulldown"),
        core_feature_keys=get_core_feature_keys("lat_pulldown"),
    ),
    ExerciseDefinition(
        key="dumbbell_shoulder_press", name="哑铃推肩", description="评估推举伸展、肩部上举、手腕肩部对齐和核心稳定。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("dumbbell_shoulder_press"),
        core_feature_keys=get_core_feature_keys("dumbbell_shoulder_press"),
    ),
    ExerciseDefinition(
        key="dumbbell_curl", name="哑铃弯举", description="评估弯举幅度和上臂稳定性。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("dumbbell_curl"),
        core_feature_keys=get_core_feature_keys("dumbbell_curl"),
    ),
    ExerciseDefinition(
        key="dumbbell_press", name="哑铃推举", description="评估推举幅度和肩部控制。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("dumbbell_press"),
        core_feature_keys=get_core_feature_keys("dumbbell_press"),
    ),
    ExerciseDefinition(
        key="russian_twist", name="俄罗斯转体", description="评估躯干旋转幅度和核心控制。",
        supported_metrics=["count", "valid_count", "score"],
        core_angles=get_core_angle_labels("russian_twist"),
        core_feature_keys=get_core_feature_keys("russian_twist"),
    ),
]


def list_exercises() -> list[ExerciseDefinition]:
    return EXERCISES
