"""Analyzer registry — maps exercise_type → analyzer class."""

from app.services.analysis.analyzers.base_analyzer import BaseExerciseAnalyzer
from app.services.analysis.analyzers.jumping_jack_analyzer import JumpingJackAnalyzer
from app.services.analysis.analyzers.plank_analyzer import PlankAnalyzer
from app.services.analysis.analyzers.push_up_analyzer import PushUpAnalyzer
from app.services.analysis.analyzers.squat_analyzer import SquatAnalyzer

ANALYZER_CLASSES: dict[str, type[BaseExerciseAnalyzer]] = {
    "squat": SquatAnalyzer,
    "push_up": PushUpAnalyzer,
    "jumping_jack": JumpingJackAnalyzer,
    "plank": PlankAnalyzer,
}

# Backwards-compatible alias used by API routes for supported exercise names.
ANALYZER_REGISTRY = ANALYZER_CLASSES


def get_analyzer(exercise_type: str) -> BaseExerciseAnalyzer:
    """Return a fresh analyzer instance for *exercise_type*."""
    if exercise_type not in ANALYZER_CLASSES:
        raise ValueError(f"Unsupported exercise_type: {exercise_type}")
    return ANALYZER_CLASSES[exercise_type]()
