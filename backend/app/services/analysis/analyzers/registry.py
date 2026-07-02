"""Analyzer registry — maps exercise_type → analyzer class (not instance!).

BIG FIX: get_analyzer() now creates a NEW instance on every call so
start_time / accumulated counters are scoped to a single session.
"""

from app.services.analysis.analyzers.base_analyzer import BaseExerciseAnalyzer
from app.services.analysis.analyzers.squat_analyzer import SquatAnalyzer
from app.services.analysis.analyzers.push_up_analyzer import PushUpAnalyzer
from app.services.analysis.analyzers.jumping_jack_analyzer import JumpingJackAnalyzer
from app.services.analysis.analyzers.plank_analyzer import PlankAnalyzer
from app.services.analysis.analyzers.lunge_analyzer import LungeAnalyzer
from app.services.analysis.analyzers.glute_bridge_analyzer import GluteBridgeAnalyzer
from app.services.analysis.analyzers.high_knees_analyzer import HighKneesAnalyzer
from app.services.analysis.analyzers.burpee_analyzer import BurpeeAnalyzer

ANALYZER_REGISTRY: dict[str, type[BaseExerciseAnalyzer]] = {
    "squat": SquatAnalyzer,
    "push_up": PushUpAnalyzer,
    "jumping_jack": JumpingJackAnalyzer,
    "plank": PlankAnalyzer,
    "lunge": LungeAnalyzer,
    "glute_bridge": GluteBridgeAnalyzer,
    "high_knees": HighKneesAnalyzer,
    "burpee": BurpeeAnalyzer,
}

# Backwards-compatible alias used by template_builder_service & syhx modules
ANALYZER_CLASSES = ANALYZER_REGISTRY


def get_analyzer(exercise_type: str) -> BaseExerciseAnalyzer:
    """Create and return a NEW analyzer instance for *exercise_type*, or raise ValueError."""
    if exercise_type not in ANALYZER_REGISTRY:
        raise ValueError(f"Unsupported exercise_type: {exercise_type}")
    return ANALYZER_REGISTRY[exercise_type]()
