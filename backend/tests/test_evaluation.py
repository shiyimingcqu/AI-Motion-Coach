"""Evaluation service tests."""

import unittest

from app.services.evaluation.calorie_service import (
    calculate_calories,
    estimate_active_seconds,
    get_exercise_display_name,
)
from app.services.evaluation.evaluation_service import build_evaluation, score_to_grade


class EvaluationServiceTests(unittest.TestCase):
    def test_active_seconds_capped_for_few_reps(self):
        active = estimate_active_seconds("squat", duration_seconds=1800, total_count=2)
        self.assertLessEqual(active, 30)

    def test_calories_two_squats_not_hundreds(self):
        calories = calculate_calories("squat", duration_seconds=1800, total_count=2)
        self.assertLess(calories, 20)

    def test_calories_reasonable_for_workout(self):
        calories = calculate_calories("squat", duration_seconds=480, total_count=20)
        self.assertGreater(calories, 5)
        self.assertLess(calories, 80)

    def test_score_to_grade(self):
        self.assertEqual(score_to_grade(95)["grade_label"], "优秀")
        self.assertEqual(score_to_grade(80)["grade_label"], "良好")
        self.assertEqual(score_to_grade(50)["grade_label"], "需改进")

    def test_build_evaluation_contains_dimensions(self):
        result = build_evaluation(
            exercise="squat",
            average_score=82,
            total_count=15,
            valid_count=12,
            error_count=3,
            duration_seconds=480,
        )
        self.assertEqual(result["exercise_name"], get_exercise_display_name("squat"))
        self.assertIn("dimension_scores", result)
        self.assertGreater(len(result["dimension_scores"]), 0)
        self.assertTrue(result["summary"])


if __name__ == "__main__":
    unittest.main()
