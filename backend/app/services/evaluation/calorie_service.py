"""Calorie estimation based on MET values and active exercise time."""

DEFAULT_WEIGHT_KG = 65.0

EXERCISE_MET: dict[str, float] = {
    "squat": 5.0,
    "push_up": 3.8,
    "plank": 3.0,
    "jumping_jack": 8.0,
    "lunge": 5.5,
    "burpee": 8.5,
    "mountain_climber": 6.0,
    "pull_up": 4.5,
    "dumbbell_curl": 3.5,
    "dumbbell_press": 4.0,
    "high_knees": 7.0,
    "russian_twist": 3.5,
    "glute_bridge": 3.0,
}

# Average seconds per rep for active-time estimation
SECONDS_PER_REP: dict[str, float] = {
    "squat": 5.0,
    "push_up": 4.0,
    "plank": 30.0,
    "jumping_jack": 2.5,
    "lunge": 5.0,
    "burpee": 6.0,
    "mountain_climber": 2.0,
    "pull_up": 5.0,
    "dumbbell_curl": 4.0,
    "dumbbell_press": 5.0,
    "high_knees": 2.0,
    "russian_twist": 3.0,
    "glute_bridge": 4.0,
}

# Per-rep calorie estimate (kcal) for 65 kg body weight
KCAL_PER_REP: dict[str, float] = {
    "squat": 0.32,
    "push_up": 0.28,
    "plank": 0.15,
    "jumping_jack": 0.18,
    "lunge": 0.30,
    "burpee": 0.45,
    "mountain_climber": 0.20,
    "pull_up": 0.35,
    "dumbbell_curl": 0.12,
    "dumbbell_press": 0.15,
    "high_knees": 0.15,
    "russian_twist": 0.10,
    "glute_bridge": 0.12,
}

EXERCISE_DISPLAY_NAMES: dict[str, str] = {
    "squat": "深蹲",
    "push_up": "俯卧撑",
    "plank": "平板支撑",
    "jumping_jack": "开合跳",
    "lunge": "弓步蹲",
    "burpee": "波比跳",
    "mountain_climber": "登山跑",
    "pull_up": "引体向上",
    "dumbbell_curl": "哑铃弯举",
    "dumbbell_press": "哑铃推举",
    "high_knees": "高抬腿",
    "russian_twist": "俄罗斯转体",
    "glute_bridge": "臀桥",
}


def get_exercise_display_name(exercise_key: str) -> str:
    return EXERCISE_DISPLAY_NAMES.get(exercise_key, exercise_key)


def estimate_active_seconds(
    exercise: str,
    duration_seconds: int,
    total_count: int,
) -> int:
    """Estimate actual exercise time, avoiding inflated wall-clock / video length."""
    duration_seconds = max(int(duration_seconds), 0)
    per_rep = SECONDS_PER_REP.get(exercise, 4.0)

    if total_count > 0:
        rep_based = int(total_count * per_rep + 15)
        return max(20, min(duration_seconds or rep_based, rep_based, 1800))

    if exercise == "plank":
        return max(30, min(duration_seconds or 60, 900))

    return max(30, min(duration_seconds or 60, 600))


def calculate_calories(
    exercise: str,
    duration_seconds: int,
    total_count: int = 0,
    weight_kg: float = DEFAULT_WEIGHT_KG,
) -> float:
    """
    Estimate calories using active exercise time + per-rep energy cost.
    Prevents long video processing time from inflating calorie totals.
    """
    met = EXERCISE_MET.get(exercise, 4.5)
    active_seconds = estimate_active_seconds(exercise, duration_seconds, total_count)
    hours = active_seconds / 3600

    time_based = met * weight_kg * hours
    rep_kcal = total_count * KCAL_PER_REP.get(exercise, 0.25)

    calories = max(time_based, rep_kcal)
    if total_count > 0:
        calories = (time_based + rep_kcal) / 2

    return round(max(calories, 0.5 if total_count > 0 else 0.1), 1)
