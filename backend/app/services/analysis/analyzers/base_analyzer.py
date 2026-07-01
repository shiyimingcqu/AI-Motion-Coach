"""Base exercise analyzer — defines the interface all exercise analyzers must implement."""

from collections import Counter, deque
import time

from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.models import NormalizedKeypoint

Keypoints = dict[str, NormalizedKeypoint]


class BaseExerciseAnalyzer:
    """Abstract base class for all exercise analyzers.

    Each analyzer implements:
      - extract_features(landmarks) -> dict   — compute angles, distances, etc.
      - detect_phase(features, state) -> str   — identify the current movement phase
      - score_frame(features, phase) -> dict   — per-frame scoring & issue detection

    The public `analyze_frame(landmarks, state)` method composes the three steps
    and returns a uniform result dict consumed by the WebSocket handler.
    """

    exercise_type: str = ""

    # Subclasses can override these for per-exercise sizing
    def __init__(self, smooth_window: int = 5):
        self.feature_history = deque(maxlen=smooth_window)
        self.start_time = time.time()

        # stage tracking
        self.stage = "ready"
        self.count = 0
        self.valid_count = 0
        self._last_down_was_valid = False
        self.scores_history: list[float] = []
        self.previous_stage = "ready"
        self.stage_stability_counter = 0
        self._rep_samples: list[dict[str, float]] = []
        self.rep_summaries: list[dict[str, float]] = []
        self.rep_results: list[dict] = []
        self.session_issue_counts: Counter[str] = Counter()
        self.session_feedback_counts: Counter[str] = Counter()

    # ─── abstract methods ────────────────────────────────────

    def extract_features(self, landmarks: Keypoints) -> dict[str, float]:
        """Compute per-frame features (angles, distances, ratios, …)."""
        raise NotImplementedError

    def detect_phase(self, features: dict, state: dict) -> str:
        """Determine the current movement phase from features + accumulated state."""
        raise NotImplementedError

    def score_frame(self, features: dict, phase: str) -> dict:
        """Return {'score': float, 'issues': list[str], 'feedback': list[str]}."""
        raise NotImplementedError

    def rep_sample_phases(self) -> tuple[str, ...]:
        """Movement phases where rep summary samples are collected."""
        return ("down", "bottom", "descending")

    def rep_completion_from_phases(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        """Return (lowering_phases, rising_phases) that mark one completed rep."""
        return (("down", "bottom", "descending"), ("up", "standing", "top_support", "ascending"))

    def rep_summary_phase(self) -> str:
        """Phase label used when scoring a completed rep summary."""
        return "bottom"

    def summarize_rep(self, samples: list[dict[str, float]]) -> dict[str, float]:
        """Collapse per-frame samples into one rep-level feature snapshot."""
        if not samples:
            return {}
        return dict(samples[-1])

    def score_rep(self, summary: dict[str, float]) -> dict:
        """Score a completed rep using summarized features."""
        return self.score_frame(summary, self.rep_summary_phase())

    def get_session_issue_counts(self) -> Counter[str]:
        return self.session_issue_counts

    def get_session_feedback_counts(self) -> Counter[str]:
        return self.session_feedback_counts

    # ─── public entry point ──────────────────────────────────

    def analyze_frame(self, landmarks: Keypoints, state: dict) -> dict:
        features = self.extract_features(landmarks)
        phase = self.detect_phase(features, state)
        current_stage = self.stage

        # smooth features via sliding window
        self.feature_history.append(features)
        smoothed = self._smooth_features()

        score_result = self.score_frame(smoothed, phase)

        lowering_phases, rising_phases = self.rep_completion_from_phases()
        rep_completed = current_stage in lowering_phases and phase in rising_phases

        if phase in self.rep_sample_phases():
            self._rep_samples.append(dict(smoothed))

        frame_issues: list[str] = []
        frame_feedback: list[str] = []
        frame_score = score_result["score"]

        if rep_completed:
            rep_summary = self.summarize_rep(self._rep_samples)
            rep_result = self.score_rep(rep_summary) if rep_summary else {
                "score": 0,
                "issues": [],
                "feedback": [],
            }
            self._last_down_was_valid = len(rep_result.get("issues", [])) == 0
            frame_issues = rep_result.get("issues", [])
            frame_feedback = rep_result.get("feedback", [])
            frame_score = rep_result.get("score", frame_score)
            for issue in frame_issues:
                self.session_issue_counts[issue] += 1
            for suggestion in frame_feedback:
                self.session_feedback_counts[suggestion] += 1
            self.rep_summaries.append(rep_summary)
            self.rep_results.append(rep_result)
            self._rep_samples = []

        # Count a rep only when we cross once from the lowering/bottom phase
        # into the rising/finished phase. Using the committed current stage
        # avoids double-counting on sequences like bottom -> up -> standing.
        if rep_completed:
            self.count += 1
            if self._last_down_was_valid:
                self.valid_count += 1
            self.scores_history.append(frame_score)

        self.previous_stage = current_stage
        self.stage = phase

        return {
            "exercise_type": self.exercise_type,
            "phase": phase,
            "count": self.count,
            "valid_count": self.valid_count,
            "features": smoothed,
            "score": frame_score,
            "issues": frame_issues,
            "feedback": frame_feedback,
            "detail_scores": score_result.get("detail_scores", {}),
        }

    def get_session_summary(self) -> dict:
        duration_seconds = int(time.time() - self.start_time)
        error_count = self.count - self.valid_count
        average_score = (
            int(sum(self.scores_history) / len(self.scores_history))
            if self.scores_history else 0
        )
        return {
            "exercise": self.exercise_type,
            "duration_seconds": duration_seconds,
            "total_count": self.count,
            "valid_count": self.valid_count,
            "error_count": error_count,
            "average_score": average_score,
        }

    # ─── helpers ─────────────────────────────────────────────

    def _smooth_features(self) -> dict[str, float]:
        if not self.feature_history:
            return {}
        smoothed: dict[str, float] = {}
        keys = self.feature_history[0].keys()
        for k in keys:
            vals = [h[k] for h in self.feature_history]
            smoothed[k] = sum(vals) / len(vals)
        return smoothed

    @staticmethod
    def _score_by_range(value: float, good_range: tuple[float, float],
                        bad_range: tuple[float, float]) -> float:
        """Continuous scoring function.

        value inside good_range → 100
        value outside bad_range → 40
        value in between → linear interpolation 40–100
        """
        good_min, good_max = good_range
        bad_min, bad_max = bad_range

        if good_min <= value <= good_max:
            return 100.0
        if value < bad_min or value > bad_max:
            return 40.0

        if bad_min <= value < good_min:
            ratio = (value - bad_min) / (good_min - bad_min)
            return 40.0 + ratio * 60.0
        if good_max < value <= bad_max:
            ratio = (bad_max - value) / (bad_max - good_max)
            return 40.0 + ratio * 60.0
        return 40.0

    @staticmethod
    def _apply_stability(current_stage: str, previous_stage: str,
                         counter: int, threshold: int = 3):
        """Debounce stage transitions."""
        if current_stage == previous_stage:
            return current_stage, 0
        new_counter = counter + 1
        if new_counter >= threshold:
            return current_stage, 0
        return previous_stage, new_counter
