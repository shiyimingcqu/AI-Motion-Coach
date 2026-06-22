import unittest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    TestClient = None

from app.main import app


@unittest.skipIf(TestClient is None, "FastAPI is not installed")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint_reports_service_status(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_exercises_endpoint_lists_supported_actions(self):
        response = self.client.get("/api/exercises")

        self.assertEqual(response.status_code, 200)
        names = {item["key"] for item in response.json()["items"]}
        self.assertTrue({"squat", "push_up", "jumping_jack", "plank"}.issubset(names))

    def test_create_analysis_task_returns_pending_task(self):
        response = self.client.post(
            "/api/analysis/tasks",
            json={"exercise": "squat", "source_uri": "storage/uploads/sample.mp4"},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["status"], "pending")
        self.assertEqual(payload["exercise"], "squat")
        self.assertTrue(payload["task_id"])


if __name__ == "__main__":
    unittest.main()
