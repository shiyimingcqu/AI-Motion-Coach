"""Base exercise analyzer — defines the interface all exercise analyzers must implement."""

from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.template_service import TemplateService
from collections import deque
import time

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
        self.current_rep_scores: list[float] = []
        self.current_rep_frames: list[dict[str, float]] = []
        self._rep_started = False
        self._seen_peak = False
        self.template_service = TemplateService()

    def reset(self):
        """Reset all internal state for a new training session."""
        self.feature_history.clear()
        self.start_time = time.time()
        self.stage = "ready"
        self.count = 0
        self.valid_count = 0
        self._last_down_was_valid = False
        self.scores_history.clear()
        self.previous_stage = "ready"
        self.stage_stability_counter = 0
        self.current_rep_scores.clear()
        self.current_rep_frames.clear()
        self._rep_started = False
        self._seen_peak = False

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

    def _should_count_rep(self, current_stage: str, phase: str) -> bool:
        """Return True when a full repetition has just completed."""
        return (
            current_stage in ("bottom", "down")
            and phase in ("up", "standing", "top_support", "ascending")
        )

    def _mark_rep_checkpoint(self, phase: str, score_result: dict) -> None:
        """Record whether the latest lowering/open phase was valid."""
        if phase in ("bottom", "open_peak", "down"):
            self._last_down_was_valid = len(score_result["issues"]) == 0

    def _track_frame_score(self, score_result: dict, phase: str) -> None:
        """Optional per-frame score accumulation (e.g. static holds)."""

    # ─── public entry point ──────────────────────────────────

    def analyze_frame(self, landmarks: Keypoints, state: dict) -> dict:
        features = self.extract_features(landmarks)
        phase = self.detect_phase(features, state)
        current_stage = self.stage

        # smooth features via sliding window
        self.feature_history.append(features)
        smoothed = self._smooth_features()

        score_result = self.score_frame(smoothed, phase)
        self._track_rep_motion(smoothed, phase, score_result["score"])
        is_rep_finished = self._is_rep_finished(current_stage, phase)
        display_score = score_result["score"]
        display_issues = score_result["issues"]
        display_feedback = score_result.get("feedback", [])
        display_detail_scores = score_result.get("detail_scores", {})

        # Count and score only after a full repetition returns to its finish phase.
        if is_rep_finished:
            rep_result = self._score_completed_rep()
            self.count += 1
            display_score = rep_result["score"]
            display_detail_scores = rep_result["detail_scores"]
            if display_score >= 75:
                self.valid_count += 1
            self.scores_history.append(display_score)
            self._reset_rep_motion()

        self._mark_rep_checkpoint(phase, score_result)
        self._track_frame_score(score_result, phase)

        self.previous_stage = current_stage
        self.stage = phase
        state["phase"] = phase

        return {
            "exercise_type": self.exercise_type,
            "phase": phase,
            "stage": phase,
            "count": self.count,
            "valid_count": self.valid_count,
            "features": smoothed,
            "metrics": smoothed,
            "score": display_score,
            "current_score": display_score,
            "issues": display_issues,
            "errors": display_issues,
            "feedback": display_feedback,
            "detail_scores": display_detail_scores,
            "is_rep_finished": is_rep_finished,
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

    def _track_rep_motion(self, features: dict[str, float], phase: str, score: float):
        active_phases = {
            "down", "bottom", "up",
            "descending", "ascending",
            "opening", "open_peak", "closing", "complete",
        }
        peak_phases = {"bottom", "open_peak"}

        if phase in active_phases:
            self._rep_started = True
        if phase in peak_phases:
            self._seen_peak = True
        if self._rep_started:
            self.current_rep_frames.append(dict(features))
            self.current_rep_scores.append(float(score))

    def _is_rep_finished(self, previous_phase: str, phase: str) -> bool:
        if not self._rep_started or not self._seen_peak:
            return False

        if self.exercise_type == "squat":
            return phase == "standing" and previous_phase in {"up", "bottom", "down"}
        if self.exercise_type == "push_up":
            return phase == "top_support" and previous_phase in {"ascending", "bottom"}
        if self.exercise_type == "jumping_jack":
            return phase in {"complete", "closed"} and previous_phase in {"closing", "open_peak"}

        return (
            phase in {"standing", "top_support", "complete", "closed"}
            and previous_phase in {"up", "ascending", "closing", "bottom", "open_peak"}
        )

    def _score_completed_rep(self) -> dict:
        scores = [s for s in self.current_rep_scores if s > 0]
        if not scores:
            return {"score": 0.0, "detail_scores": {}}

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        fallback_score = round(avg_score * 0.7 + min_score * 0.3, 1)
        try:
            template_result = self.template_service.score_by_template(
                self.exercise_type,
                self.current_rep_frames,
            )
            sequence_score = float(template_result.get("score", 0.0))
            if sequence_score > 0:
                detail_scores = template_result.get("detail_scores", {})
                detail_scores["frame_average"] = round(avg_score, 1)
                detail_scores["weakest_phase"] = round(min_score, 1)
                detail_scores["template_sequence"] = round(sequence_score, 1)
                display_score = max(sequence_score, fallback_score - 5)
                return {
                    "score": round(display_score, 1),
                    "detail_scores": detail_scores,
                }
        except Exception:
            pass

        return {
            "score": fallback_score,
            "detail_scores": {
                "sequence_average": round(avg_score, 1),
                "weakest_phase": round(min_score, 1),
            },
        }

    def _reset_rep_motion(self):
        self.current_rep_scores.clear()
        self.current_rep_frames.clear()
        self._rep_started = False
        self._seen_peak = False

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
