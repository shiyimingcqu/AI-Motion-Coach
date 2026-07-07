"""Base exercise analyzer — defines the interface all exercise analyzers must implement."""

from collections import Counter, deque
import time

from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.template_service import TemplateService, get_active_template_id

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
        self._frame_score_sum = 0.0
        self._frame_score_count = 0
        self.previous_stage = "ready"
        self.stage_stability_counter = 0
        self._rep_samples: list[dict[str, float]] = []
        self.rep_summaries: list[dict[str, float]] = []
        self.rep_results: list[dict] = []
        self.session_issue_counts: Counter[str] = Counter()
        self.session_feedback_counts: Counter[str] = Counter()

        # Frame-level tracking for rep_segments (按单次动作筛选回放)
        self._frame_index: int = 0
        self._last_rep_completed_count: int = -1
        self._rep_start_frame_index: int = 0
        self._rep_standing_frame: int = 0
        self.rep_segments: list[dict] = []
        self.rep_nodes: list[dict] = []
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
        self._frame_score_sum = 0.0
        self._frame_score_count = 0
        self.previous_stage = "ready"
        self.stage_stability_counter = 0
        self._frame_index = 0
        self._last_rep_completed_count = -1
        self._rep_start_frame_index = 0
        self._rep_standing_frame = 0
        self._rep_samples = []
        self.rep_summaries = []
        self.rep_results = []
        self.rep_segments = []
        self.rep_nodes = []
        self.session_issue_counts = Counter()
        self.session_feedback_counts = Counter()

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

    def score_rep_by_active_template(self, samples: list[dict[str, float]]) -> dict | None:
        """Return a template score for one completed rep when an active template exists."""
        active_template_id = get_active_template_id(self.exercise_type)
        if not active_template_id or not samples:
            return None
        try:
            template_result = self.template_service.score_by_template(
                self.exercise_type,
                samples,
                active_template_id,
            )
        except (FileNotFoundError, ValueError):
            return None
        fair_threshold = float(template_result.get("fair_threshold", 60) or 60)
        return {
            "score": template_result.get("score", 0),
            "score_source": "template",
            "template_id": template_result.get("template_id") or active_template_id,
            "template_detail_scores": template_result.get("detail_scores", {}),
            "template_differences": template_result.get("differences", {}),
            "template_level": template_result.get("level"),
            "fair_threshold": fair_threshold,
            "is_valid": float(template_result.get("score", 0) or 0) >= fair_threshold,
        }

    def get_session_issue_counts(self) -> Counter[str]:
        return self.session_issue_counts

    def get_session_feedback_counts(self) -> Counter[str]:
        return self.session_feedback_counts

    # ─── metric inference for rep_segment issues ─────────────

    @staticmethod
    def _infer_metric_from_issue(issue: str) -> str | None:
        """Try to infer a metric name from Chinese issue text."""
        if not issue:
            return None
        if "膝" in issue or "蹲" in issue:
            return "knee_angle"
        if "躯干" in issue or "前倾" in issue or "塌腰" in issue:
            return "trunk_angle"
        if "肘" in issue:
            return "elbow_angle"
        if "臀" in issue or "髋" in issue:
            return "hip_angle"
        if "肩" in issue:
            return "shoulder_abduction_angle"
        if "对称" in issue:
            return "knee_symmetry_diff"
        if "身体" in issue or "直线" in issue:
            return "body_line_angle"
        if "踝" in issue or "脚" in issue:
            return "ankle_distance"
        return None

    # ─── public entry point ──────────────────────────────────

    def analyze_frame(self, landmarks: Keypoints, state: dict, frame_index: int | None = None) -> dict:
        if frame_index is not None:
            self._frame_index = frame_index

        features = self.extract_features(landmarks)
        phase = self.detect_phase(features, state)
        current_stage = self.stage

        # smooth features via sliding window
        self.feature_history.append(features)
        smoothed = self._smooth_features()

        score_result = self.score_frame(smoothed, phase)

        lowering_phases, rising_phases = self.rep_completion_from_phases()
        rep_completed = current_stage in lowering_phases and phase in rising_phases
        if rep_completed and self._last_rep_completed_count == self.count + 1:
            rep_completed = False

        frame_issues: list[str] = []
        frame_feedback: list[str] = []
        frame_score = score_result["score"]
        self._record_frame_score(frame_score)
        score_source = "rule"
        template_score_payload: dict | None = None

        # Rep segment tracking
        if phase == "standing":
            # Capture the last standing frame before next rep starts
            self._rep_standing_frame = self._frame_index

        if phase in self.rep_sample_phases():
            if not self._rep_samples:
                # First down/bottom frame — start from the last standing frame
                self._rep_start_frame_index = getattr(self, "_rep_standing_frame", self._frame_index)
            self._rep_samples.append(dict(smoothed))

        if rep_completed:
            # End frame: extend to standing (captured on next standing visit)
            # but for rep filtering, include at least the down→up range
            end_frame = self._frame_index
            standing = getattr(self, "_rep_standing_frame", -1)
            if standing > self._rep_start_frame_index:
                end_frame = standing
            rep_summary = self.summarize_rep(self._rep_samples)
            rep_result = self.score_rep(rep_summary) if rep_summary else {
                "score": 0,
                "issues": [],
                "feedback": [],
            }
            template_score_payload = self.score_rep_by_active_template(self._rep_samples)
            if template_score_payload is not None:
                rep_result = {
                    **rep_result,
                    "score": template_score_payload["score"],
                    "score_source": "template",
                    "template_id": template_score_payload.get("template_id"),
                    "template_detail_scores": template_score_payload.get("template_detail_scores", {}),
                    "template_differences": template_score_payload.get("template_differences", {}),
                }
                self._last_down_was_valid = bool(template_score_payload.get("is_valid"))
                score_source = "template"
            else:
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

            # Record rep segment before clearing samples
            rep_issues: list[dict] = []
            rep_issue_texts = rep_result.get("issues", [])
            rep_feedback_texts = rep_result.get("feedback", [])
            for i, issue_text in enumerate(rep_issue_texts):
                suggestion = rep_feedback_texts[i] if i < len(rep_feedback_texts) else ""
                metric = self._infer_metric_from_issue(issue_text)
                rep_issues.append({
                    "issue": issue_text,
                    "suggestion": suggestion,
                    "severity": "warning",
                    "metric": metric or "",
                    "value": rep_summary.get(metric, 0) if metric else 0,
                })

            self.rep_segments.append({
                "rep_index": self.count + 1,
                "start_frame_index": self._rep_start_frame_index,
                "end_frame_index": max(end_frame, self._frame_index),
                "score": rep_result.get("score", 0),
                "issues": rep_issues,
            })
            self.rep_nodes.append({
                "rep_index": self.count + 1,
                "frame_index": self._frame_index,
                "start_frame_index": self._rep_start_frame_index,
                "score": rep_result.get("score", 0),
                "issues": rep_issues,
            })

            self._rep_samples = []

        # Count a rep only when we cross once from the lowering/bottom phase
        # into the rising/finished phase. Using the committed current stage
        # avoids double-counting on sequences like bottom -> up -> standing.
        if rep_completed:
            self.count += 1
            self._last_rep_completed_count = self.count
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
            "score_source": score_source,
            "template_id": template_score_payload.get("template_id") if template_score_payload else None,
            "template_detail_scores": template_score_payload.get("template_detail_scores", {}) if template_score_payload else {},
            "template_differences": template_score_payload.get("template_differences", {}) if template_score_payload else {},
            "issues": frame_issues,
            "feedback": frame_feedback,
            "detail_scores": score_result.get("detail_scores", {}),
        }

    def _record_frame_score(self, score: float) -> None:
        """累积实时帧评分，供平板支撑/未完成计次等场景计算 session 均分。"""
        if isinstance(score, (int, float)) and score > 0:
            self._frame_score_sum += float(score)
            self._frame_score_count += 1

    def _resolve_average_score(self) -> int:
        if self.scores_history:
            return int(round(sum(self.scores_history) / len(self.scores_history)))
        if self._frame_score_count > 0:
            return int(round(self._frame_score_sum / self._frame_score_count))
        if self.rep_results:
            rep_scores = [
                float(item["score"])
                for item in self.rep_results
                if isinstance(item.get("score"), (int, float)) and item["score"] > 0
            ]
            if rep_scores:
                return int(round(sum(rep_scores) / len(rep_scores)))
        return 0

    def get_session_summary(self) -> dict:
        duration_seconds = int(time.time() - self.start_time)
        error_count = self.count - self.valid_count
        average_score = self._resolve_average_score()
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
