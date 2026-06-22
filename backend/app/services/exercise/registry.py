from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ExerciseDefinition:
    key: str
    name: str
    description: str
    supported_metrics: list[str]

    def to_dict(self):
        return asdict(self)


EXERCISES = [
    ExerciseDefinition(
        key="squat",
        name="深蹲",
        description="评估下蹲深度、膝盖方向和躯干稳定性。",
        supported_metrics=["count", "valid_count", "score", "depth_ratio"],
    ),
    ExerciseDefinition(
        key="push_up",
        name="俯卧撑",
        description="评估屈臂幅度、撑起锁定和身体直线。",
        supported_metrics=["count", "valid_count", "score"],
    ),
    ExerciseDefinition(
        key="jumping_jack",
        name="开合跳",
        description="评估开合幅度、节奏和完整度。",
        supported_metrics=["count", "valid_count", "score"],
    ),
    ExerciseDefinition(
        key="plank",
        name="平板支撑",
        description="评估髋部高度、躯干直线和保持时长。",
        supported_metrics=["duration", "score", "error_count"],
    ),
]


def list_exercises() -> list[ExerciseDefinition]:
    return EXERCISES
