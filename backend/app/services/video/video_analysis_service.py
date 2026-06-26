from dataclasses import asdict
from pathlib import Path
from uuid import uuid4
import time

import cv2

from app.core.config import settings
from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.angle_feature_service import extract_squat_features
from app.services.analysis.template_service import TemplateService
from app.services.analysis.feedback_service import FeedbackService
from app.services.analysis.models import NormalizedKeypoint
from app.services.session.session_service import session_service


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
        width = self._even_dimension(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640)
        height = self._even_dimension(int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480)
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"VP80"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise ValueError("Cannot open browser-compatible video writer")

        pose = self._create_pose()
        analyzer = ExerciseAnalyzer(exercise=exercise)
        frame_index = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break

            annotated = self._annotate_frame(frame, pose, exercise, frame_index)
            
            if pose is not None:
                self._analyze_frame(annotated, pose, analyzer)
            
            if annotated.shape[1] != width or annotated.shape[0] != height:
                annotated = cv2.resize(annotated, (width, height))
            writer.write(annotated)
            frame_index += 1

        capture.release()
        writer.release()

        if pose is not None:
            pose.close()

        session_summary = analyzer.get_session_summary()
        if session_summary["total_count"] > 0:
            session_service.create_session(
                exercise=session_summary["exercise"],
                duration_seconds=session_summary["duration_seconds"],
                total_count=session_summary["total_count"],
                valid_count=session_summary["valid_count"],
                error_count=session_summary["error_count"],
                average_score=session_summary["average_score"],
            )

        return str(output_path).replace("\\", "/")

    def run_realtime_video_test(
        self,
        source_uri: str,
        exercise: str,
        max_frames: int = 120,
        keypoint_extractor=None,
    ) -> dict:
        source_path = self._resolve_source(source_uri)
        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {source_uri}")

        video_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        analyzer = ExerciseAnalyzer(exercise=exercise)
        template_service = TemplateService()
        feedback_service = FeedbackService()
        pose = self._create_pose()
        frame_results = []
        frame_index = 0
        limit = max(1, min(int(max_frames), 600))

        try:
            while frame_index < limit:
                ok, frame = capture.read()
                if not ok:
                    break

                if keypoint_extractor is not None:
                    keypoints = keypoint_extractor(frame, pose)
                elif pose is not None:
                    keypoints = self._extract_keypoints_from_frame(frame, pose)
                else:
                    keypoints = {}

                result = analyzer.analyze(keypoints)
                payload = result.to_dict()
                payload["frame_index"] = frame_index
                payload["keypoints"] = {k: asdict(v) for k, v in keypoints.items()}

                # 如果是深蹲动作，添加角度指标
                if exercise == "squat" and keypoints:
                    try:
                        metrics = extract_squat_features(keypoints)
                        payload["metrics"] = metrics
                    except ValueError:
                        pass

                frame_results.append(payload)
                frame_index += 1
        finally:
            capture.release()
            if pose is not None:
                pose.close()

        # 计算模板评分
        template_score = None
        if exercise == "squat" and frame_results:
            try:
                # 提取所有帧的 metrics
                frames_with_metrics = [
                    frame.get("metrics", {}) for frame in frame_results
                    if frame.get("metrics")
                ]

                if frames_with_metrics:
                    score_result = template_service.score_by_template(exercise, frames_with_metrics)
                    feedback = feedback_service.generate_template_feedback(score_result)

                    template_score = {
                        "score": score_result["score"],
                        "level": score_result["level"],
                        "detail_scores": score_result["detail_scores"],
                        "differences": score_result["differences"],
                        "errors": feedback["errors"],
                        "suggestions": feedback["suggestions"]
                    }
            except Exception:
                # 模板评分失败不影响整体流程
                pass

        return {
            "exercise": exercise,
            "source_uri": str(source_path).replace("\\", "/"),
            "processed_frames": len(frame_results),
            "video_width": video_width,
            "video_height": video_height,
            "frames": frame_results,
            "summary": analyzer.get_session_summary(),
            "template_score": template_score,
        }

    def _analyze_frame(self, frame, pose, analyzer):
        keypoints = self._extract_keypoints_from_frame(frame, pose)
        if keypoints:
            analyzer.analyze(keypoints)

    def _extract_keypoints_from_frame(self, frame, pose):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = pose.process(rgb)

        if not result.pose_landmarks:
            return {}

        keypoints = {}
        landmark_names = [
            "nose", "left_eye_inner", "left_eye", "left_eye_outer",
            "right_eye_inner", "right_eye", "right_eye_outer",
            "left_ear", "right_ear", "mouth_left", "mouth_right",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_pinky", "right_pinky",
            "left_index", "right_index", "left_thumb", "right_thumb",
            "left_hip", "right_hip", "left_knee", "right_knee",
            "left_ankle", "right_ankle", "left_heel", "right_heel",
            "left_foot_index", "right_foot_index"
        ]

        for i, name in enumerate(landmark_names):
            if i < len(result.pose_landmarks.landmark):
                landmark = result.pose_landmarks.landmark[i]
                keypoints[name] = NormalizedKeypoint(
                    x=landmark.x,
                    y=landmark.y,
                    visibility=landmark.visibility
                )

        return keypoints

    def _resolve_source(self, source_uri: str) -> Path:
        source = Path(source_uri)
        if source.is_absolute():
            return source
        return (Path.cwd() / source).resolve()

    def _make_output_path(self, source_path: Path) -> Path:
        return self.storage_root / "outputs" / f"{source_path.stem}-{uuid4().hex[:8]}.webm"

    @staticmethod
    def _even_dimension(value: int) -> int:
        return value if value % 2 == 0 else value - 1

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
