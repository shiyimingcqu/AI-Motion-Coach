"""Analyzer registry — maps exercise_type → analyzer class."""

from app.services.analysis.analyzers.base_analyzer import BaseExerciseAnalyzer
from app.services.analysis.analyzers.burpee_analyzer import BurpeeAnalyzer
from app.services.analysis.analyzers.dumbbell_curl_analyzer import DumbbellCurlAnalyzer
from app.services.analysis.analyzers.dumbbell_press_analyzer import DumbbellPressAnalyzer
from app.services.analysis.analyzers.glute_bridge_analyzer import GluteBridgeAnalyzer
from app.services.analysis.analyzers.high_knees_analyzer import HighKneesAnalyzer
from app.services.analysis.analyzers.jumping_jack_analyzer import JumpingJackAnalyzer
from app.services.analysis.analyzers.lunge_analyzer import LungeAnalyzer
from app.services.analysis.analyzers.mountain_climber_analyzer import MountainClimberAnalyzer
from app.services.analysis.analyzers.plank_analyzer import PlankAnalyzer
from app.services.analysis.analyzers.pull_up_analyzer import PullUpAnalyzer
from app.services.analysis.analyzers.push_up_analyzer import PushUpAnalyzer
from app.services.analysis.analyzers.russian_twist_analyzer import RussianTwistAnalyzer
from app.services.analysis.analyzers.squat_analyzer import SquatAnalyzer

ANALYZER_CLASSES: dict[str, type[BaseExerciseAnalyzer]] = {
    "squat": SquatAnalyzer,
    "push_up": PushUpAnalyzer,
    "jumping_jack": JumpingJackAnalyzer,
    "plank": PlankAnalyzer,
    "lunge": LungeAnalyzer,
    "glute_bridge": GluteBridgeAnalyzer,
    "high_knees": HighKneesAnalyzer,
    "burpee": BurpeeAnalyzer,
    "mountain_climber": MountainClimberAnalyzer,
    "pull_up": PullUpAnalyzer,
    "dumbbell_curl": DumbbellCurlAnalyzer,
    "dumbbell_press": DumbbellPressAnalyzer,
    "russian_twist": RussianTwistAnalyzer,
}

# Backwards-compatible alias used by API routes for supported exercise names.
ANALYZER_REGISTRY = ANALYZER_CLASSES


def get_analyzer(exercise_type: str) -> BaseExerciseAnalyzer:
    """Return a fresh analyzer instance for *exercise_type*."""
    if exercise_type not in ANALYZER_CLASSES:
        raise ValueError(f"Unsupported exercise_type: {exercise_type}")
    return ANALYZER_CLASSES[exercise_type]()
