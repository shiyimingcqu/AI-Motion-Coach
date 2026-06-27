from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CoreMetricDefinition:
    label: str
    feature_key: str

    def to_dict(self) -> dict:
        return asdict(self)


EXERCISE_CORE_METRICS: dict[str, list[CoreMetricDefinition]] = {
    "squat": [
        CoreMetricDefinition(label="膝角", feature_key="knee_angle"),
        CoreMetricDefinition(label="髋角", feature_key="hip_angle"),
        CoreMetricDefinition(label="躯干倾斜角", feature_key="trunk_angle"),
        CoreMetricDefinition(label="左右膝差", feature_key="knee_symmetry_diff"),
    ],
    "push_up": [
        CoreMetricDefinition(label="肘角", feature_key="elbow_angle"),
        CoreMetricDefinition(label="肩角", feature_key="shoulder_angle"),
        CoreMetricDefinition(label="身体直线角", feature_key="body_line_angle"),
        CoreMetricDefinition(label="髋部塌陷角", feature_key="hip_sag_angle"),
    ],
    "plank": [
        CoreMetricDefinition(label="肩髋踝直线角", feature_key="body_line_angle"),
        CoreMetricDefinition(label="髋部角", feature_key="hip_angle"),
        CoreMetricDefinition(label="颈部角", feature_key="neck_angle"),
    ],
    "jumping_jack": [
        CoreMetricDefinition(label="肩外展角", feature_key="shoulder_abduction_angle"),
        CoreMetricDefinition(label="双腿夹角", feature_key="leg_spread_angle"),
        CoreMetricDefinition(label="手腕高度", feature_key="wrist_height"),
        CoreMetricDefinition(label="脚踝距离", feature_key="ankle_distance"),
    ],
}


def get_core_metrics(exercise: str) -> list[CoreMetricDefinition]:
    return EXERCISE_CORE_METRICS.get(exercise, [])


def get_core_angle_labels(exercise: str) -> list[str]:
    return [metric.label for metric in get_core_metrics(exercise)]


def get_core_feature_keys(exercise: str) -> list[str]:
    return [metric.feature_key for metric in get_core_metrics(exercise)]


def build_default_weights(exercise: str) -> dict[str, float]:
    feature_keys = get_core_feature_keys(exercise)
    if not feature_keys:
        return {}

    weight = round(1 / len(feature_keys), 4)
    return {feature_key: weight for feature_key in feature_keys}
