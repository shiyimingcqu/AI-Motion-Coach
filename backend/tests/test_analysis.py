import unittest

from app.services.analysis.angle_calculator import calculate_angle
from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint


class AnalysisTests(unittest.TestCase):
    def test_calculate_angle_returns_right_angle(self):
        angle = calculate_angle((1, 0), (0, 0), (0, 1))

        self.assertEqual(round(angle, 2), 90.0)

    def test_squat_analyzer_counts_rep_after_down_to_up_transition(self):
        analyzer = ExerciseAnalyzer(exercise="squat")

        down_frame = {
            "left_hip": NormalizedKeypoint(x=0.45, y=0.72, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.66, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.72, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.66, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }
        up_frame = {
            "left_hip": NormalizedKeypoint(x=0.45, y=0.24, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.58, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.24, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.58, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }

        analyzer.analyze(down_frame)
        result = analyzer.analyze(up_frame)

        self.assertEqual(result.stage, "up")
        self.assertEqual(result.count, 1)
        self.assertEqual(result.valid_count, 1)
        self.assertGreaterEqual(result.score, 80)

    def test_squat_analyzer_flags_insufficient_depth(self):
        analyzer = ExerciseAnalyzer(exercise="squat")
        shallow_frame = {
            "left_hip": NormalizedKeypoint(x=0.45, y=0.40, visibility=0.99),
            "left_knee": NormalizedKeypoint(x=0.47, y=0.62, visibility=0.99),
            "left_ankle": NormalizedKeypoint(x=0.47, y=0.82, visibility=0.99),
            "right_hip": NormalizedKeypoint(x=0.55, y=0.40, visibility=0.99),
            "right_knee": NormalizedKeypoint(x=0.53, y=0.62, visibility=0.99),
            "right_ankle": NormalizedKeypoint(x=0.53, y=0.82, visibility=0.99),
        }

        result = analyzer.analyze(shallow_frame)

        self.assertIn("下蹲深度不足", result.errors)
        self.assertLess(result.score, 90)


if __name__ == "__main__":
    unittest.main()
