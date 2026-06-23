import unittest

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:
    TestClient = None

from app.main import app
from app.api.routes import realtime


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

    def test_realtime_websocket_handles_empty_keypoints_without_crashing(self):
        with self.client.websocket_connect("/api/realtime/pose") as websocket:
            websocket.send_json({"type": "start", "exercise": "squat"})
            started = websocket.receive_json()
            self.assertEqual(started["type"], "status")
            self.assertEqual(started["state"], "running")

            websocket.send_json({"type": "frame", "exercise": "squat", "keypoints": {}})
            result = websocket.receive_json()

            self.assertEqual(result["type"], "analysis")
            self.assertEqual(result["stage"], "invalid")
            self.assertIn("关键点不足", result["errors"])

    def test_realtime_websocket_analyzes_frames_and_saves_session_on_finish(self):
        before = len(self.client.get("/api/sessions").json()["items"])
        down_frame = {
            "left_hip": {"x": 0.45, "y": 0.72, "visibility": 0.99},
            "left_knee": {"x": 0.47, "y": 0.66, "visibility": 0.99},
            "left_ankle": {"x": 0.47, "y": 0.82, "visibility": 0.99},
            "right_hip": {"x": 0.55, "y": 0.72, "visibility": 0.99},
            "right_knee": {"x": 0.53, "y": 0.66, "visibility": 0.99},
            "right_ankle": {"x": 0.53, "y": 0.82, "visibility": 0.99},
        }
        up_frame = {
            "left_hip": {"x": 0.45, "y": 0.24, "visibility": 0.99},
            "left_knee": {"x": 0.47, "y": 0.58, "visibility": 0.99},
            "left_ankle": {"x": 0.47, "y": 0.82, "visibility": 0.99},
            "right_hip": {"x": 0.55, "y": 0.24, "visibility": 0.99},
            "right_knee": {"x": 0.53, "y": 0.58, "visibility": 0.99},
            "right_ankle": {"x": 0.53, "y": 0.82, "visibility": 0.99},
        }

        with self.client.websocket_connect("/api/realtime/pose") as websocket:
            websocket.send_json({"type": "start", "exercise": "squat"})
            websocket.receive_json()
            websocket.send_json({"type": "frame", "exercise": "squat", "keypoints": down_frame})
            websocket.receive_json()
            websocket.send_json({"type": "frame", "exercise": "squat", "keypoints": up_frame})
            result = websocket.receive_json()
            websocket.send_json({"type": "finish"})
            summary = websocket.receive_json()

        after = self.client.get("/api/sessions").json()["items"]
        self.assertEqual(result["count"], 1)
        self.assertEqual(summary["type"], "summary")
        self.assertEqual(summary["session"]["total_count"], 1)
        self.assertEqual(len(after), before + 1)

    def test_realtime_video_test_endpoint_accepts_uploaded_video(self):
        original = realtime.video_analysis_service.run_realtime_video_test
        captured = {}

        def fake_video_test(source_uri, exercise, max_frames=120):
            captured["source_uri"] = source_uri
            captured["exercise"] = exercise
            captured["max_frames"] = max_frames
            return {
                "exercise": exercise,
                "source_uri": source_uri,
                "processed_frames": 1,
                "frames": [{"frame_index": 0, "stage": "invalid", "count": 0}],
                "summary": {"exercise": exercise, "total_count": 0},
            }

        realtime.video_analysis_service.run_realtime_video_test = fake_video_test
        try:
            response = self.client.post(
                "/api/realtime/video-test",
                data={"exercise": "squat", "max_frames": "12"},
                files={"file": ("sample.mp4", b"video-bytes", "video/mp4")},
            )
        finally:
            realtime.video_analysis_service.run_realtime_video_test = original

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["exercise"], "squat")
        self.assertEqual(payload["processed_frames"], 1)
        self.assertEqual(captured["exercise"], "squat")
        self.assertEqual(captured["max_frames"], 12)
        self.assertIn("storage", captured["source_uri"])


if __name__ == "__main__":
    unittest.main()
