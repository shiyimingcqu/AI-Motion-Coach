"""Analyzer registry — maps exercise_type → analyzer instance."""

from app.services.analysis.analyzers.base_analyzer import BaseExerciseAnalyzer
from app.services.analysis.analyzers.squat_analyzer import SquatAnalyzer
from app.services.analysis.analyzers.push_up_analyzer import PushUpAnalyzer
from app.services.analysis.analyzers.jumping_jack_analyzer import JumpingJackAnalyzer
from app.services.analysis.analyzers.plank_analyzer import PlankAnalyzer

ANALYZER_REGISTRY: dict[str, BaseExerciseAnalyzer] = {
    "squat": SquatAnalyzer(),
    "push_up": PushUpAnalyzer(),
    "jumping_jack": JumpingJackAnalyzer(),
    "plank": PlankAnalyzer(),
}


def get_analyzer(exercise_type: str) -> BaseExerciseAnalyzer:
    """Return the analyzer for *exercise_type*, or raise ValueError."""
    if exercise_type not in ANALYZER_REGISTRY:
        raise ValueError(f"Unsupported exercise_type: {exercise_type}")
    return ANALYZER_REGISTRY[exercise_type]
