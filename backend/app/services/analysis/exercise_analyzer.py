"""Unified exercise analyzer — legacy wrapper that delegates to the registry.

New code should use `analyzers.registry.get_analyzer()` directly.
This file is kept for backwards compatibility.
"""

from app.services.analysis.analyzers.registry import get_analyzer
from app.services.analysis.models import AnalysisResult

Keypoints = dict[str, "NormalizedKeypoint"]


class ExerciseAnalyzer:
    """Legacy wrapper. Delegates to the registry-based analyzer.

    Keeps the same `.analyze(keypoints)` → `AnalysisResult` interface
    so existing callers (WebSocket handler, video tests) still work.
    """

    def __init__(self, exercise: str = "squat"):
        self.exercise = exercise
        self._analyzer = get_analyzer(exercise)
        self._frame_state: dict = {}
        self.stage = "ready"
        self.count = 0
        self.valid_count = 0
        self._last_down_was_valid = False
        self.scores_history: list[float] = []
        self.start_time = 0.0  # set by the real-time loop

    def analyze(self, keypoints: Keypoints) -> AnalysisResult:
        result = self._analyzer.analyze_frame(keypoints, self._frame_state)
        self.stage = result["phase"]
        self.count = result["count"]
        self.valid_count = result["valid_count"]
        self.scores_history.append(result["score"])

        return AnalysisResult(
            exercise=self.exercise,
            stage=result["phase"],
            count=result["count"],
            valid_count=result["valid_count"],
            score=result["score"],
            errors=result["issues"],
            features=result.get("features", {}),
        )

    def get_session_summary(self) -> dict:
        return self._analyzer.get_session_summary()
