class ReportService:
    def personal_summary(self):
        return {
            "average_score": 88,
            "total_sessions": 1,
            "trend": [{"date": "2026-06-22", "score": 88}],
            "errors": [{"name": "下蹲深度不足", "count": 4}],
        }

    def class_summary(self):
        return {
            "student_count": 1,
            "average_score": 88,
            "exercise_distribution": [{"exercise": "squat", "count": 1}],
        }


report_service = ReportService()
