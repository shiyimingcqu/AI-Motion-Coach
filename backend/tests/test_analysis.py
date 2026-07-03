import unittest

from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.analyzers.registry import get_analyzer
from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint


class AnalysisTests(unittest.TestCase):
    def test_calculate_angle_returns_right_angle(self):
        angle = calculate_angle((1, 0), (0, 0), (0, 1))

        self.assertEqual(round(angle, 2), 90.0)

    def test_squat_analyzer_counts_rep_after_down_to_up_transition(self):
        analyzer = get_analyzer("squat")
        state: dict = {}

        down_frame = {
            "left_shoulder": NormalizedKeypoint(x=0.45, y=0.20, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.55, y=0.20, visibility=0.99),
            "left_hip": NormalizedKeypoint(x=0.45, y=0.72, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.66, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.72, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.66, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }
        up_frame = {
            "left_shoulder": NormalizedKeypoint(x=0.45, y=0.20, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.55, y=0.20, visibility=0.99),
            "left_hip": NormalizedKeypoint(x=0.45, y=0.24, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.58, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.24, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.58, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }

        analyzer.analyze_frame(down_frame, state)
        result = analyzer.analyze_frame(up_frame, state)

        self.assertIn(result["phase"], ("up", "standing"))
        self.assertEqual(result["count"], 1)
        self.assertGreaterEqual(result["score"], 0)

    def test_squat_summarize_rep_uses_minimum_knee_angle(self):
        analyzer = get_analyzer("squat")
        samples = [
            {"knee_angle": 150.0, "hip_angle": 130.0, "trunk_angle": 15.0, "knee_symmetry_diff": 5.0},
            {"knee_angle": 90.0, "hip_angle": 100.0, "trunk_angle": 15.0, "knee_symmetry_diff": 5.0},
            {"knee_angle": 130.0, "hip_angle": 125.0, "trunk_angle": 15.0, "knee_symmetry_diff": 5.0},
        ]

        summary = analyzer.summarize_rep(samples)

        self.assertEqual(summary["knee_angle"], 90.0)

    def test_squat_rep_summary_flags_shallow_depth(self):
        analyzer = get_analyzer("squat")
        summary = {
            "knee_angle": 130.0,
            "hip_angle": 130.0,
            "trunk_angle": 15.0,
            "knee_symmetry_diff": 5.0,
        }

        result = analyzer.score_rep(summary)

        self.assertIn("下蹲深度偏浅", result["issues"])
        self.assertLess(result["score"], 90)

    def test_squat_session_resolves_conflicting_depth_advice(self):
        analyzer = get_analyzer("squat")
        analyzer.session_issue_counts["下蹲深度偏浅"] = 1
        analyzer.session_issue_counts["下蹲深度偏深"] = 1
        analyzer.session_feedback_counts["下次下蹲到大腿接近水平即可，不要只做半蹲"] = 1
        analyzer.session_feedback_counts[
            "下蹲到大腿接近水平或略低即可，避免为追求深度丢失稳定"
        ] = 1

        issues = analyzer.get_session_issue_counts()
        suggestions = analyzer.get_session_feedback_counts()

        self.assertNotIn("下蹲深度偏浅", issues)
        self.assertNotIn("下蹲深度偏深", issues)
        self.assertIn("下蹲深度不稳定", issues)
        self.assertIn("每次下蹲都控制到大腿接近水平，避免忽深忽浅", suggestions)

    def test_squat_analyzer_ignores_transition_frame_issues(self):
        analyzer = get_analyzer("squat")
        state: dict = {}
        shoulders = {
            "left_shoulder": NormalizedKeypoint(x=0.45, y=0.20, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.55, y=0.20, visibility=0.99),
        }
        transition_frame = {
            **shoulders,
            "left_hip": NormalizedKeypoint(x=0.45, y=0.50, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.58, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.50, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.58, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }

        transition_result = analyzer.analyze_frame(transition_frame, state)

        self.assertEqual(transition_result["issues"], [])
        self.assertEqual(len(analyzer.get_session_issue_counts()), 0)

    def test_exercise_analyzer_preserves_frame_state_for_rep_count(self):
        analyzer = ExerciseAnalyzer(exercise="squat")
        shoulders = {
            "left_shoulder": NormalizedKeypoint(x=0.45, y=0.20, visibility=0.99),
            "right_shoulder": NormalizedKeypoint(x=0.55, y=0.20, visibility=0.99),
        }
        down_frame = {
            **shoulders,
            "left_hip": NormalizedKeypoint(x=0.45, y=0.72, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.66, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.72, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.66, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }
        up_frame = {
            **shoulders,
            "left_hip": NormalizedKeypoint(x=0.45, y=0.24, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.58, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.24, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.58, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }

        analyzer.analyze(down_frame)
        result = analyzer.analyze(up_frame)

        self.assertEqual(result.count, 1)
        self.assertEqual(analyzer.get_session_summary()["total_count"], 1)

    def test_build_unified_feedback_from_raw_analyzer(self):
        from app.services.analysis.unified_feedback_service import (
            build_unified_feedback_from_analyzer,
        )

        analyzer = get_analyzer("squat")
        analyzer.rep_summaries.append(
            {
                "knee_angle": 130.0,
                "trunk_angle": 15.0,
                "knee_symmetry_diff": 5.0,
                "max_knee_angle_step": 10.0,
            }
        )
        analyzer.count = 1
        analyzer.valid_count = 0

        feedback = build_unified_feedback_from_analyzer(analyzer)
        issues = [item["issue"] for item in feedback["items"] if item["issue"]]

        self.assertIn("下蹲深度整体偏浅", issues)

    def test_push_up_summarize_rep_uses_minimum_elbow_angle(self):
        analyzer = get_analyzer("push_up")
        samples = [
            {"elbow_angle": 150.0, "body_line_angle": 5.0, "hip_sag_angle": 4.0, "symmetry_diff": 3.0},
            {"elbow_angle": 88.0, "body_line_angle": 8.0, "hip_sag_angle": 6.0, "symmetry_diff": 4.0},
            {"elbow_angle": 120.0, "body_line_angle": 6.0, "hip_sag_angle": 5.0, "symmetry_diff": 3.0},
        ]

        summary = analyzer.summarize_rep(samples)

        self.assertEqual(summary["elbow_angle"], 88.0)

    def test_push_up_rep_summary_flags_shallow_depth(self):
        analyzer = get_analyzer("push_up")
        summary = {
            "elbow_angle": 115.0,
            "body_line_angle": 8.0,
            "hip_sag_angle": 6.0,
            "symmetry_diff": 4.0,
            "max_elbow_angle_step": 8.0,
        }

        result = analyzer.score_rep(summary)

        self.assertIn("下降幅度不足", result["issues"])
        self.assertLess(result["score"], 90)

    def test_jumping_jack_summarize_rep_uses_peak_spread(self):
        analyzer = get_analyzer("jumping_jack")
        samples = [
            {"spread_ratio": 2.0, "wrist_height": 0.10, "shoulder_abduction_angle": 90.0, "arm_angle_diff": 4.0},
            {"spread_ratio": 4.5, "wrist_height": 0.28, "shoulder_abduction_angle": 155.0, "arm_angle_diff": 5.0},
            {"spread_ratio": 3.2, "wrist_height": 0.20, "shoulder_abduction_angle": 120.0, "arm_angle_diff": 6.0},
        ]

        summary = analyzer.summarize_rep(samples)

        self.assertEqual(summary["spread_ratio"], 4.5)

    def test_jumping_jack_rep_summary_flags_insufficient_arm_raise(self):
        analyzer = get_analyzer("jumping_jack")
        summary = {
            "spread_ratio": 4.0,
            "wrist_height": 0.08,
            "shoulder_abduction_angle": 100.0,
            "arm_angle_diff": 5.0,
            "max_spread_step": 0.5,
        }

        result = analyzer.score_rep(summary)

        self.assertIn("手臂上举幅度不足", result["issues"])
        self.assertLess(result["score"], 85)

    def test_plank_score_rep_flags_poor_body_line(self):
        analyzer = get_analyzer("plank")
        summary = {
            "body_line_angle": 22.0,
            "hip_sag_angle": 18.0,
            "elbow_offset": 0.04,
            "max_body_jitter": 6.0,
        }

        result = analyzer.score_rep(summary)

        self.assertIn("塌腰或撅臀明显，身体未保持直线", result["issues"])
        self.assertLess(result["score"], 80)

    def test_plank_holding_phase_scores_positive(self):
        analyzer = get_analyzer("plank")
        features = {
            "body_line_angle": 5.0,
            "hip_sag_angle": 7.0,
            "elbow_offset": 0.03,
            "neck_angle": 55.0,
        }

        result = analyzer.score_frame(features, "holding")

        self.assertGreaterEqual(result["score"], 75)
        self.assertEqual(result["issues"], [])

    def test_registry_includes_all_exercises(self):
        expected = {
            "squat", "push_up", "jumping_jack", "plank",
            "lunge", "glute_bridge", "high_knees", "burpee",
            "mountain_climber", "pull_up", "dumbbell_curl",
            "dumbbell_press", "russian_twist",
        }
        from app.services.analysis.analyzers.registry import ANALYZER_CLASSES

        self.assertEqual(set(ANALYZER_CLASSES.keys()), expected)
        for key in expected:
            analyzer = get_analyzer(key)
            self.assertEqual(analyzer.exercise_type, key)

    def test_lunge_rep_summary_flags_shallow_depth(self):
        analyzer = get_analyzer("lunge")
        result = analyzer.score_rep({
            "knee_angle": 115.0,
            "max_trunk_angle": 14.0,
            "max_knee_symmetry_diff": 12.0,
            "max_knee_angle_step": 12.0,
        })
        self.assertIn("弓步下蹲深度不足", result["issues"])

    def test_glute_bridge_rep_summary_flags_low_extension(self):
        analyzer = get_analyzer("glute_bridge")
        result = analyzer.score_rep({
            "hip_angle": 145.0,
            "min_body_line_angle": 6.0,
            "max_hip_angle_step": 15.0,
        })
        self.assertIn("抬臀高度不足", result["issues"])

    def test_high_knees_rep_summary_flags_low_height(self):
        analyzer = get_analyzer("high_knees")
        result = analyzer.score_rep({
            "knee_height": 0.08,
            "knee_angle": 110.0,
            "max_left_knee_h": 0.09,
            "max_right_knee_h": 0.08,
            "max_height_step": 0.05,
        })
        self.assertIn("抬膝高度不足", result["issues"])

    def test_burpee_rep_summary_flags_shallow_squat(self):
        analyzer = get_analyzer("burpee")
        result = analyzer.score_rep({
            "min_hip_angle": 130.0,
            "plank_body_line_angle": 18.0,
            "max_wrist_height": 0.20,
        })
        self.assertIn("下蹲阶段深度不足", result["issues"])


if __name__ == "__main__":
    unittest.main()
