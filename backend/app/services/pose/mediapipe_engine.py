from app.services.pose.engine import PoseEngine


class MediaPipePoseEngine(PoseEngine):
    def __init__(self):
        self._pose = None

    def infer(self, frame):
        try:
            import mediapipe as mp
        except ModuleNotFoundError as exc:
            raise RuntimeError("MediaPipe is not installed") from exc

        if self._pose is None:
            self._pose = mp.solutions.pose.Pose(static_image_mode=False)

        result = self._pose.process(frame)
        if not result.pose_landmarks:
            return {}

        return {
            str(index): {
                "x": landmark.x,
                "y": landmark.y,
                "visibility": landmark.visibility,
            }
            for index, landmark in enumerate(result.pose_landmarks.landmark)
        }
