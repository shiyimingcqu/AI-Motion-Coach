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
]


def list_exercises() -> list[ExerciseDefinition]:
    return EXERCISES
