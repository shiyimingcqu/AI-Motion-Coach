"""Unified exercise analyzer — legacy wrapper that delegates to the registry.

Integrates with UnifiedFeedbackService for consistent feedback across
real-time detection and video analysis.
"""

from app.services.analysis.analyzers.registry import get_analyzer
from app.services.analysis.models import AnalysisResult
from app.services.analysis.unified_feedback_service import (
    UnifiedFeedbackResult,
    build_unified_feedback_from_analyzer,
    unified_feedback_service,
)

Keypoints = dict[str, "NormalizedKeypoint"]


class ExerciseAnalyzer:
    """Unified analyzer with consistent feedback generation.

    Uses UnifiedFeedbackService to ensure real-time detection and video analysis
    produce the same feedback format. AI advice only does language polishing.
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
        self.start_time = 0.0

    def analyze(self, keypoints: Keypoints) -> AnalysisResult:
        result = self._analyzer.analyze_frame(keypoints, self._frame_state)
        self.stage = result["phase"]
        self.count = result["count"]
        self.valid_count = result["valid_count"]

        return AnalysisResult(
            exercise=self.exercise,
            stage=result["phase"],
            count=result["count"],
            valid_count=result["valid_count"],
            score=result["score"],
            errors=result["issues"],
            feedback=result.get("feedback", []),
            features=result.get("features", {}),
        )

    def get_session_summary(self) -> dict:
        return self._analyzer.get_session_summary()

    def get_session_issue_counts(self):
        return self._analyzer.get_session_issue_counts()

    def get_session_feedback_counts(self):
        return self._analyzer.get_session_feedback_counts()

    def get_unified_feedback(self) -> UnifiedFeedbackResult:
        """获取统一的结构化反馈（用于 AI 建议包装）。"""
        return build_unified_feedback_from_analyzer(self._analyzer)

    def get_ai_advice_payload(self) -> dict:
        """获取 AI 建议所需的结构化数据（统一格式）。"""
        feedback = self.get_unified_feedback()
        return unified_feedback_service.format_for_ai(feedback)
