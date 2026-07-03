import os

from app.services.pose.engine import PoseEngine


class MediaPipePoseEngine(PoseEngine):
    def __init__(self):
        self._pose = None
        self._model_path = os.path.expanduser("~/.pose_eval/pose_landmarker.task")

    def _ensure_pose(self):
        if self._pose is not None:
            return
        if not os.path.exists(self._model_path):
            raise FileNotFoundError(f"Pose landmarker model not found: {self._model_path}")
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision

        base_options = mp_python.BaseOptions(model_asset_path=self._model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._pose = vision.PoseLandmarker.create_from_options(options)

    def infer(self, frame):
        self._ensure_pose()
        import mediapipe as mp
        import cv2

        if frame.shape[-1] == 3 and frame.ndim == 3:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            rgb = frame

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._pose.detect(mp_image)

        if not result.pose_landmarks:
            return {}

        landmarks = result.pose_landmarks[0]
        return {
            str(index): {
                "x": landmark.x,
                "y": landmark.y,
                "visibility": landmark.visibility,
            }
            for index, landmark in enumerate(landmarks)
        }
