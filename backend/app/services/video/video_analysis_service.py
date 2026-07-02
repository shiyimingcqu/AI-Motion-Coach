import json
import os
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import cv2
import mediapipe as mp

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import SessionORM
from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.template_service import TemplateService
from app.services.analysis.unified_feedback_service import unified_feedback_service
from app.services.session.session_service import session_service

# landmark names consistent with MediaPipe Pose (33 landmarks)
_LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

def _new_pose_landmarker():
    """Create a fresh PoseLandmarker instance.

    NEVER cache across calls — mediapipe requires monotonically
    increasing timestamps per instance for VIDEO mode, so reusing
    a landmarker across separate video runs will always fail.
    """
    model_path = os.path.expanduser("~/.pose_eval/pose_landmarker.task")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Pose landmarker model not found at {model_path}. "
            "Please download it first."
        )

    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)


def _process_pose_on_frame(frame, pose, timestamp_ms: int):
    """Run PoseLandmarker on a single frame. Returns PoseLandmarkerResult or None."""
    if pose is None:
        return None
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    return pose.detect_for_video(mp_image, timestamp_ms)


def _extract_keypoints_from_pose_result(pose_result) -> dict:
    """Convert PoseLandmarkerResult → {name: NormalizedKeypoint} dict."""
    if pose_result is None or not pose_result.pose_landmarks:
        return {}

    # pose_landmarks is a list of NormalizedLandmarkList; take the first person
    landmarks = pose_result.pose_landmarks[0]

    keypoints = {}
    for index, name in enumerate(_LANDMARK_NAMES):
        if index >= len(landmarks):
            break
        lm = landmarks[index]
        keypoints[name] = NormalizedKeypoint(
            x=lm.x, y=lm.y, visibility=lm.visibility,
        )
    return keypoints


def _annotate_frame(frame, pose_result, exercise: str, frame_index: int):
    """Draw pose landmarks and overlay text on a frame."""
    from mediapipe.tasks.python import vision

    annotated = frame.copy()

    if pose_result is not None and pose_result.pose_landmarks:
        vision.drawing_utils.draw_landmarks(
            annotated,
            pose_result.pose_landmarks[0],
            vision.PoseLandmarksConnections.POSE_LANDMARKS,
            vision.drawing_styles.get_default_pose_landmarks_style(),
        )

    cv2.rectangle(annotated, (12, 12), (360, 92), (18, 32, 26), -1)
    cv2.putText(annotated, f"Exercise: {exercise}", (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (242, 184, 75), 2, cv2.LINE_AA)
    cv2.putText(annotated, f"Frame: {frame_index}", (24, 74),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (215, 239, 227), 2, cv2.LINE_AA)
    return annotated


class VideoAnalysisService:
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        self.default_max_frames = 120

    # ---------- public API ----------

    def analyze_video(
        self, source_uri: str, exercise: str,
        user_id: int | None = None,
    ) -> dict:
        """视频上传分析：分析 + 渲染标注视频。"""
        analysis = self.run_realtime_video_test(
            source_uri=source_uri, exercise=exercise,
            max_frames=self.default_max_frames,
            persist_session=True, user_id=user_id,
        )
        output_uri = self._render_annotated_video(
            source_uri=source_uri, exercise=exercise,
            max_frames=self.default_max_frames,
        )
        return {
            "output_uri": output_uri,
            "session_id": analysis.get("session_id"),
            "processed_frames": analysis["processed_frames"],
            "summary": analysis["summary"],
            "issues": analysis["issues"],
            "suggestions": analysis["suggestions"],
            "unified_feedback": analysis["unified_feedback"],
        }

    def run_realtime_video_test(
        self, source_uri: str, exercise: str,
        max_frames: int = 120, keypoint_extractor=None,
        persist_session: bool = False, user_id: int | None = None,
    ) -> dict:
        source_path = self._resolve_source(source_uri)
        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {source_uri}")

        video_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = capture.get(cv2.CAP_PROP_FPS) or 30

        analyzer = ExerciseAnalyzer(exercise=exercise)
        template_service = TemplateService()
        pose = _new_pose_landmarker()
        frame_results: list = []
        limit = max(1, min(int(max_frames), 600))

        try:
            for frame_index, frame in self._iter_capture_frames(capture, limit):
                timestamp_ms = int(frame_index * 1000 / fps)
                if keypoint_extractor is not None:
                    keypoints = keypoint_extractor(frame, pose, timestamp_ms)
                else:
                    pose_result = _process_pose_on_frame(frame, pose, timestamp_ms)
                    keypoints = _extract_keypoints_from_pose_result(pose_result)

                if not keypoints:
                    continue

                try:
                    result = analyzer.analyze(keypoints)
                except ValueError:
                    continue
                payload = result.to_dict()
                payload["frame_index"] = frame_index
                payload["keypoints"] = {key: asdict(value) for key, value in keypoints.items()}
                if payload.get("features"):
                    payload["metrics"] = payload["features"]
                frame_results.append(payload)
        finally:
            capture.release()

        analysis = self._build_analysis_response(
            analyzer=analyzer,
            output_uri=str(source_path).replace("\\", "/"),
            processed_frames=len(frame_results),
            persist_session=persist_session,
            user_id=user_id,
        )
        formatted_feedback = {
            "errors": analysis["issues"],
            "feedbacks": analysis["suggestions"],
        }

        template_score = None
        if frame_results:
            try:
                frames_with_metrics = [
                    frame.get("metrics", {})
                    for frame in frame_results
                    if frame.get("metrics")
                ]
                if frames_with_metrics:
                    score_result = template_service.score_by_template(exercise, frames_with_metrics)
                    template_score = {
                        "score": score_result["score"],
                        "level": score_result["level"],
                        "detail_scores": score_result["detail_scores"],
                        "differences": score_result["differences"],
                        "errors": formatted_feedback["errors"],
                        "suggestions": formatted_feedback["feedbacks"],
                    }
            except Exception:
                pass

        return {
            "exercise": exercise,
            "source_uri": str(source_path).replace("\\", "/"),
            "processed_frames": len(frame_results),
            "video_width": video_width,
            "video_height": video_height,
            "frames": frame_results,
            "summary": analysis["summary"],
            "session_id": analysis.get("session_id"),
            "template_score": template_score,
            "unified_feedback": {
                **analysis["unified_feedback"],
                "errors": formatted_feedback["errors"],
                "feedbacks": formatted_feedback["feedbacks"],
            },
            "issues": analysis["issues"],
            "suggestions": analysis["suggestions"],
        }

    # ---------- annotated video ----------

    def _render_annotated_video(
        self, source_uri: str, exercise: str, max_frames: int = 120,
    ) -> str:
        source_path = self._resolve_source(source_uri)
        output_path = self._make_output_path(source_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {source_uri}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 24
        width = self._even_dimension(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640)
        height = self._even_dimension(int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480)
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"VP80"),
            fps, (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise ValueError("Cannot open browser-compatible video writer")

        pose = _new_pose_landmarker()
        limit = max(1, min(int(max_frames), 600))

        try:
            for frame_index, frame in self._iter_capture_frames(capture, limit):
                timestamp_ms = int(frame_index * 1000 / fps)
                pose_result = _process_pose_on_frame(frame, pose, timestamp_ms)
                annotated = _annotate_frame(frame, pose_result, exercise, frame_index)
                if annotated.shape[1] != width or annotated.shape[0] != height:
                    annotated = cv2.resize(annotated, (width, height))
                writer.write(annotated)
        finally:
            capture.release()
            writer.release()

        return str(output_path).replace("\\", "/")

    # ---------- session persistence ----------

    def _build_analysis_response(
        self, analyzer: ExerciseAnalyzer,
        output_uri: str, processed_frames: int,
        persist_session: bool, user_id: int | None = None,
    ) -> dict:
        session_summary = analyzer.get_session_summary()
        unified_feedback = analyzer.get_unified_feedback()
        formatted_feedback = unified_feedback_service.format_for_ai(unified_feedback)
        session_id: str | None = None

        if persist_session and session_summary["total_count"] > 0:
            session = session_service.create_session(
                exercise=session_summary["exercise"],
                duration_seconds=session_summary["duration_seconds"],
                total_count=session_summary["total_count"],
                valid_count=session_summary["valid_count"],
                error_count=session_summary["error_count"],
                average_score=session_summary["average_score"],
                user_id=user_id,
            )
            session_id = session.session_id
            try:
                self._save_feedback_summary(session_id, formatted_feedback)
            except Exception:
                pass

        return {
            "output_uri": output_uri,
            "session_id": session_id,
            "processed_frames": processed_frames,
            "summary": session_summary,
            "issues": formatted_feedback["errors"],
            "suggestions": formatted_feedback["feedbacks"],
            "unified_feedback": {
                "score": unified_feedback["summary_score"],
                "level": unified_feedback["summary_level"],
                "total_reps": unified_feedback["total_reps"],
                "valid_reps": unified_feedback["valid_reps"],
                "items": [
                    {"issue": item["issue"], "suggestion": item["suggestion"], "severity": item["severity"]}
                    for item in unified_feedback["items"]
                ],
            },
        }

    def _save_feedback_summary(self, session_id: str, formatted_feedback: dict) -> None:
        feedback_data = {
            "issues": formatted_feedback["errors"],
            "suggestions": formatted_feedback["feedbacks"],
            "metrics": formatted_feedback["metrics"],
            "score": formatted_feedback["score"],
            "level": formatted_feedback["level"],
        }
        db = SessionLocal()
        try:
            sess = db.query(SessionORM).filter(SessionORM.session_id == session_id).first()
            if sess:
                sess.feedback_summary = json.dumps(feedback_data, ensure_ascii=False)
                db.commit()
        finally:
            db.close()

    # ---------- helpers ----------

    @staticmethod
    def _iter_capture_frames(capture: cv2.VideoCapture, limit: int):
        frame_index = 0
        while frame_index < limit:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame_index, frame
            frame_index += 1

    @staticmethod
    def _resolve_source(source_uri: str) -> Path:
        source = Path(source_uri)
        if source.is_absolute():
            return source
        return (Path.cwd() / source).resolve()

    def _make_output_path(self, source_path: Path) -> Path:
        return self.storage_root / "outputs" / f"{source_path.stem}-{uuid4().hex[:8]}.webm"

    @staticmethod
    def _even_dimension(value: int) -> int:
        return value if value % 2 == 0 else value - 1


video_analysis_service = VideoAnalysisService(settings.storage_root)
