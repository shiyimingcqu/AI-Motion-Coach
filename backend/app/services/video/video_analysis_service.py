from pathlib import Path
from uuid import uuid4

import cv2

from app.core.config import settings


class VideoAnalysisService:
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)

    def analyze_video(self, source_uri: str, exercise: str) -> str:
        source_path = self._resolve_source(source_uri)
        output_path = self._make_output_path(source_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {source_uri}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 24
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )

        pose = self._create_pose()
        frame_index = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            annotated = self._annotate_frame(frame, pose, exercise, frame_index)
            writer.write(annotated)
            frame_index += 1

        capture.release()
        writer.release()

        if pose is not None:
            pose.close()

        return str(output_path).replace("\\", "/")

    def _resolve_source(self, source_uri: str) -> Path:
        source = Path(source_uri)
        if source.is_absolute():
            return source
        return (Path.cwd() / source).resolve()

    def _make_output_path(self, source_path: Path) -> Path:
        suffix = source_path.suffix if source_path.suffix else ".mp4"
        return self.storage_root / "outputs" / f"{source_path.stem}-{uuid4().hex[:8]}{suffix}"

    @staticmethod
    def _create_pose():
        try:
            import mediapipe as mp
        except ModuleNotFoundError:
            return None

        return mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def _annotate_frame(self, frame, pose, exercise: str, frame_index: int):
        annotated = frame.copy()

        if pose is not None:
            self._draw_pose(annotated, pose)

        cv2.rectangle(annotated, (12, 12), (360, 92), (18, 32, 26), -1)
        cv2.putText(
            annotated,
            f"Exercise: {exercise}",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (242, 184, 75),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            f"Frame: {frame_index}",
            (24, 74),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (215, 239, 227),
            2,
            cv2.LINE_AA,
        )
        return annotated

    @staticmethod
    def _draw_pose(frame, pose):
        import mediapipe as mp

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)
        if not result.pose_landmarks:
            return

        mp.solutions.drawing_utils.draw_landmarks(
            frame,
            result.pose_landmarks,
            mp.solutions.pose.POSE_CONNECTIONS,
            mp.solutions.drawing_styles.get_default_pose_landmarks_style(),
        )


video_analysis_service = VideoAnalysisService(settings.storage_root)
