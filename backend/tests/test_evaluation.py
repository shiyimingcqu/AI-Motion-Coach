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

    def test_personal_summary_sorts_trend_by_date(self):
        from app.services.report.report_service import report_service
        from unittest.mock import MagicMock

        sessions = []
        for day, score in [("2026-07-01", 60.0), ("2026-07-03", 80.0), ("2026-07-02", 70.0)]:
            session = MagicMock()
            session.exercise = "squat"
            session.duration_seconds = 60
            session.total_count = 5
            session.valid_count = 4
            session.error_count = 1
            session.average_score = score
            session.evaluation_json = None
            session.created_at = __import__("datetime").datetime.fromisoformat(f"{day}T10:00:00")
            sessions.append(session)

        report_service._query_sessions = lambda *args, **kwargs: sessions
        summary = report_service.personal_summary(user_id=2)
        dates = [item["date"] for item in summary["trend"]]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(summary["total_sessions"], 3)

    def test_build_evaluation_all_exercises(self):
        for exercise, name in [
            ("squat", "深蹲"),
            ("push_up", "俯卧撑"),
            ("jumping_jack", "开合跳"),
            ("plank", "平板支撑"),
        ]:
            result = build_evaluation(
                exercise=exercise,
                average_score=78,
                total_count=10,
                valid_count=8,
                error_count=2,
                duration_seconds=300,
            )
            self.assertEqual(result["exercise_name"], name)
            self.assertGreater(len(result["dimension_scores"]), 0)
            self.assertTrue(result["summary"])


if __name__ == "__main__":
    unittest.main()
