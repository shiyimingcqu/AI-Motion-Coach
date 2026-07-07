import json
from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

import cv2

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import SessionORM
from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.template_service import TemplateService
from app.services.analysis.unified_feedback_service import unified_feedback_service
from app.services.session.session_service import session_service


class VideoAnalysisService:
    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)
        # 默认上限与网页端约 10fps 采样接近；短于上限时读全片
        self.default_max_frames = 240

    def analyze_video(
        self,
        source_uri: str,
        exercise: str,
        user_id: int | None = None,
    ) -> dict:
        """视频上传分析：与 run_realtime_video_test 共用同一套帧分析逻辑。"""
        analysis = self.run_realtime_video_test(
            source_uri=source_uri,
            exercise=exercise,
            max_frames=self.default_max_frames,
            persist_session=True,
            user_id=user_id,
        )
        output_uri = ""
        try:
            output_uri = self._render_annotated_video(
                source_uri=source_uri,
                exercise=exercise,
                max_frames=self.default_max_frames,
            )
        except Exception:
            # 标注视频生成失败不影响分析结果（Windows 上 VP80 编码器常不可用）
            output_uri = ""
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
        self,
        source_uri: str,
        exercise: str,
        max_frames: int = 120,
        keypoint_extractor=None,
        persist_session: bool = False,
        user_id: int | None = None,
    ) -> dict:
        source_path = self._resolve_source(source_uri)
        capture = cv2.VideoCapture(str(source_path))
        if not capture.isOpened():
            raise ValueError(f"Cannot open video: {source_uri}")

        video_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

        analyzer = ExerciseAnalyzer(exercise=exercise)
        template_service = TemplateService()
        pose = self._create_pose()
        frame_results = []
        limit = max(1, min(int(max_frames), 600))

        try:
            for frame_index, frame in self._iter_capture_frames(capture, limit):
                if keypoint_extractor is not None:
                    keypoints = keypoint_extractor(frame, pose)
                elif pose is not None:
                    keypoints = self._extract_keypoints_from_frame(frame, pose)
                else:
                    keypoints = {}

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
            if pose is not None:
                pose.close()

        analysis = self._build_analysis_response(
            analyzer=analyzer,
            output_uri=str(source_path).replace("\\", "/"),
            processed_frames=len(frame_results),
            persist_session=persist_session,
            user_id=user_id,
            frame_results=frame_results,
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

    def _render_annotated_video(
        self,
        source_uri: str,
        exercise: str,
        max_frames: int = 120,
    ) -> str:
        """生成带骨架标注的输出视频（不影响分析结果）。"""
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
        limit = max(1, min(int(max_frames), 600))

        try:
            for frame_index, frame in self._iter_capture_frames(capture, limit):
                pose_result = self._process_pose_on_frame(frame, pose) if pose is not None else None
                annotated = self._annotate_frame(frame, pose_result, exercise, frame_index)
                if annotated.shape[1] != width or annotated.shape[0] != height:
                    annotated = cv2.resize(annotated, (width, height))
                writer.write(annotated)
        finally:
            capture.release()
            writer.release()
            if pose is not None:
                pose.close()

        return str(output_path).replace("\\", "/")

    def _build_analysis_response(
        self,
        analyzer: ExerciseAnalyzer,
        output_uri: str,
        processed_frames: int,
        persist_session: bool,
        user_id: int | None = None,
        frame_results: list | None = None,
    ) -> dict:
        from app.services.report.error_frame_service import (
            extract_video_error_snapshots,
            extract_video_highlight_snapshots,
        )

        session_summary = analyzer.get_session_summary()
        unified_feedback = analyzer.get_unified_feedback()
        formatted_feedback = unified_feedback_service.format_for_ai(unified_feedback)
        session_id: str | None = None

        has_analysis_signal = (
            session_summary["total_count"] > 0
            or processed_frames > 0
            or bool(formatted_feedback.get("errors"))
            or bool(unified_feedback.get("items"))
        )
        if persist_session and has_analysis_signal:
            error_snapshots = extract_video_error_snapshots(
                frame_results or [],
                float(session_summary["average_score"]),
            )
            highlight_snapshots = extract_video_highlight_snapshots(
                frame_results or [],
                float(session_summary["average_score"]),
            )
            session = session_service.create_session(
                exercise=session_summary["exercise"],
                duration_seconds=session_summary["duration_seconds"],
                total_count=session_summary["total_count"],
                valid_count=session_summary["valid_count"],
                error_count=session_summary["error_count"],
                average_score=session_summary["average_score"],
                user_id=user_id,
                pose_replay_meta={
                    "source": "video_analysis",
                    "processed_frames": processed_frames,
                    "error_snapshots": error_snapshots,
                    "highlight_snapshots": highlight_snapshots,
                },
            )
            session_id = session.session_id
            try:
                self._save_feedback_summary(
                    session_id,
                    formatted_feedback,
                    unified_feedback,
                    session_summary["exercise"],
                )
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
                    {
                        "issue": item["issue"],
                        "suggestion": item["suggestion"],
                        "severity": item["severity"],
                    }
                    for item in unified_feedback["items"]
                ],
            },
        }

    def _save_feedback_summary(
        self,
        session_id: str,
        formatted_feedback: dict,
        unified_feedback: dict | None = None,
        exercise: str = "squat",
    ) -> None:
        from app.services.session.feedback_persistence import (
            build_feedback_data,
            save_session_feedback_summary,
        )

        feedback_data = build_feedback_data(unified_feedback or {}, formatted_feedback)
        save_session_feedback_summary(
            session_id,
            feedback_data,
            generate_ai_async=True,
            exercise=exercise,
        )

    @staticmethod
    def _iter_capture_frames(capture: cv2.VideoCapture, limit: int):
        """均匀抽取整段视频帧，避免只读开头导致漏掉动作（与网页播完整个视频对齐）。"""
        limit = max(1, int(limit))
        total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        if total <= 0:
            frame_index = 0
            while frame_index < limit:
                ok, frame = capture.read()
                if not ok:
                    break
                yield frame_index, frame
                frame_index += 1
            return

        if total <= limit:
            for frame_index in range(total):
                ok, frame = capture.read()
                if not ok:
                    break
                yield frame_index, frame
            return

        if limit == 1:
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = capture.read()
            if ok:
                yield 0, frame
            return

        for sample_index in range(limit):
            frame_index = int(round(sample_index * (total - 1) / (limit - 1)))
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                continue
            yield frame_index, frame

    def _process_pose_on_frame(self, frame, pose):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return pose.process(rgb)

    def _extract_keypoints_from_frame(self, frame, pose):
        pose_result = self._process_pose_on_frame(frame, pose)
        return self._extract_keypoints_from_pose_result(pose_result)

    def _extract_keypoints_from_pose_result(self, pose_result):
        if pose_result is None or not pose_result.pose_landmarks:
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
            "left_foot_index", "right_foot_index",
        ]

        for index, name in enumerate(landmark_names):
            if index < len(pose_result.pose_landmarks.landmark):
                landmark = pose_result.pose_landmarks.landmark[index]
                keypoints[name] = NormalizedKeypoint(
                    x=landmark.x,
                    y=landmark.y,
                    visibility=landmark.visibility,
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

    def _annotate_frame(self, frame, pose_result, exercise: str, frame_index: int):
        annotated = frame.copy()

        if pose_result is not None and pose_result.pose_landmarks:
            import mediapipe as mp

            mp.solutions.drawing_utils.draw_landmarks(
                annotated,
                pose_result.pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_pose_landmarks_style(),
            )

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


video_analysis_service = VideoAnalysisService(settings.storage_root)
