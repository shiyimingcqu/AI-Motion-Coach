"""Realtime analysis WebSocket and HTTP endpoints — multi-exercise support."""

import os
import time
from pathlib import Path

from app.api.deps import get_current_active_user
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import UserORM
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.analyzers.registry import get_analyzer, ANALYZER_REGISTRY
from app.services.analysis.exercise_metrics import get_core_metrics
from app.services.storage.local_storage import local_storage
from app.services.session.session_service import session_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Query
except ModuleNotFoundError:
    APIRouter = None
    File = Form = HTTPException = UploadFile = WebSocket = WebSocketDisconnect = Query = None

try:
    import cv2
    import numpy as np
    import base64
except ModuleNotFoundError:
    cv2 = None
    np = None
    base64 = None

router = APIRouter(prefix="/realtime", tags=["realtime"]) if APIRouter else None
_pose_detect_states: dict[str, dict] = {}


def _parse_keypoints(raw_keypoints: dict) -> dict[str, NormalizedKeypoint]:
    return {
        name: NormalizedKeypoint(
            x=value["x"],
            y=value["y"],
            visibility=value.get("visibility", 1.0),
        )
        for name, value in raw_keypoints.items()
    }


# Module-level MediaPipe PoseLandmarker instance (lazy init, reused across requests)
_landmarker = None


def _find_pose_landmarker_model() -> Path:
    candidates = [
        Path(__file__).resolve().parents[3] / "pose_landmarker_lite.task",
        Path(r"C:\temp\pose_landmarker_lite.task"),
        Path(__file__).resolve().parents[4] / "frontend" / "public" / "mediapipe" / "models" / "pose_landmarker_lite.task",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise RuntimeError(
        "pose_landmarker_lite.task not found. Tried: "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def _get_landmarker():
    """Get or create the MediaPipe PoseLandmarker instance (singleton)."""
    global _landmarker
    if _landmarker is None:
        try:
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

            # 模型文件（避免中文路径，MediaPipe C++ 层不支持）
            model_path = r"C:\temp\pose_landmarker_lite.task"
            if not os.path.exists(model_path):
                raise RuntimeError(f"模型文件不存在: {model_path}")

            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.3,
                min_pose_presence_confidence=0.3,
                min_tracking_confidence=0.3,
            )
            _landmarker = PoseLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"MediaPipe 初始化失败: {e}")
    return _landmarker


def _get_landmarker():
    """Get or create the MediaPipe PoseLandmarker instance (singleton)."""
    global _landmarker
    if _landmarker is None:
        try:
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

            model_path = _find_pose_landmarker_model()
            model_buffer = model_path.read_bytes()

            options = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_buffer=model_buffer),
                running_mode=RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.3,
                min_pose_presence_confidence=0.3,
                min_tracking_confidence=0.3,
            )
            _landmarker = PoseLandmarker.create_from_options(options)
        except Exception as e:
            raise RuntimeError(f"MediaPipe 初始化失败: {e}")
    return _landmarker


if router:
    @router.get("/analyzers")
    def list_analyzers(
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """Return the list of supported exercise types."""
        return {"items": list(ANALYZER_REGISTRY.keys())}

    @router.post("/analyze-frame")
    async def analyze_frame(
        request: dict,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """
        Analyze a single frame for any supported exercise.

        Request:
        {
            "exercise_type": "squat",
            "keypoints": { ... }
        }
        """
        started_at = time.perf_counter()
        exercise_type = request.get("exercise_type", "squat")
        raw_keypoints = request.get("keypoints", {})

        try:
            analyzer = get_analyzer(exercise_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        try:
            keypoints = _parse_keypoints(raw_keypoints)
            features = analyzer.extract_features(keypoints)
            return {"exercise_type": exercise_type, "features": features}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/video-test", status_code=201)
    async def realtime_video_test(
        exercise: str = Form("squat"),
        max_frames: int = Form(120),
        file: UploadFile = File(...),
    ):
        try:
            source_uri = await local_storage.save_upload(file)
            return video_analysis_service.run_realtime_video_test(
                source_uri=source_uri,
                exercise=exercise,
                max_frames=max_frames,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=f"视频文件路径不存在: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"视频分析失败: {exc}") from exc

    @router.post("/score-action", status_code=200)
    async def score_action(
        request: dict,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """
        Score a sequence of user frames against a template.

        Request:
        {
            "action": "squat",
            "template_id": "optional_template_id",
            "frames": [ { "knee_angle": ..., ... } ]
        }
        """
        from app.services.analysis.template_service import TemplateService

        action = request.get("action", "squat")
        template_id = request.get("template_id")
        frames = request.get("frames", [])

        if len(frames) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 frames for scoring")

        try:
            ts = TemplateService(
                template_dir="app/templates",
                storage_dir="storage/templates",
            )
            result = ts.score_by_template(action, frames, template_id)
            result["action"] = action
            try:
                tf = ts._find_template_file(action)
                result["template_id"] = template_id or (tf.stem if tf else None)
            except Exception:
                result["template_id"] = template_id or None
            result["is_partial"] = len(frames) < 50
        except (FileNotFoundError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return result

    @router.post("/pose-detect")
    async def pose_detect(
        request: dict = Body(...),
    ):
        """
        接收 base64 图片帧，运行 MediaPipe Pose，返回关键点和特征。

        Request:
        {
            "exercise_type": "squat",
            "frames": [{"image": "base64_jpeg_data"}, ...]
        }

        Response:
        {
            "frames": [{
                "keypoints": [{"x":0.5,"y":0.3,"z":0,"visibility":0.99}, ...],  # 33点
                "features": {"knee_angle":120.5,...}
            }, ...]
        }
        """
        started_at = time.perf_counter()
        if cv2 is None or np is None or base64 is None:
            raise HTTPException(status_code=500, detail="cv2/numpy 不可用")

        exercise_type = request.get("exercise_type", "squat")
        frames = request.get("frames", [])
        if exercise_type == "jumping_jack" and request.get("reset_state"):
            _pose_detect_states[exercise_type] = {}
            try:
                get_analyzer(exercise_type).reset()
            except Exception:
                pass

        if not frames:
            raise HTTPException(status_code=400, detail="frames 不能为空")

        try:
            analyzer = get_analyzer(exercise_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        # 获取 MediaPipe Pose 单例
        try:
            landmarker = _get_landmarker()
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

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

        results = []
        for frame_data in frames:
            try:
                image_b64 = frame_data.get("image", "")
                if not image_b64:
                    results.append({"keypoints": None, "features": None})
                    continue

                # 解码 base64 图片
                try:
                    img_bytes = base64.b64decode(image_b64)
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    if img is None:
                        results.append({"keypoints": None, "features": None})
                        continue
                except Exception:
                    results.append({"keypoints": None, "features": None})
                    continue

                # MediaPipe 处理（新 Tasks API）
                from mediapipe import Image, ImageFormat
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
                mp_result = landmarker.detect(mp_image)

                if not mp_result.pose_landmarks:
                    results.append({"keypoints": None, "features": None, "error": "未检测到人体"})
                    continue

                # 提取 33 关键点
                landmarks = mp_result.pose_landmarks[0]
                keypoints = []
                for i in range(33):
                    if i < len(landmarks):
                        lm = landmarks[i]
                        keypoints.append({
                            "x": round(lm.x, 6),
                            "y": round(lm.y, 6),
                            "z": round(lm.z, 6),
                            "visibility": round(lm.visibility, 6),
                        })
                    else:
                        keypoints.append({"x": 0, "y": 0, "z": 0, "visibility": 0})

                # 构建 NormalizedKeypoint 字典用于特征提取
                named_keypoints = {}
                for idx, name in enumerate(landmark_names):
                    if idx < len(landmarks):
                        lm = landmarks[idx]
                        named_keypoints[name] = NormalizedKeypoint(
                            x=lm.x, y=lm.y, visibility=lm.visibility
                        )

                # 提取动作特征
                features = None
                analysis = None
                try:
                    features = analyzer.extract_features(named_keypoints)
                except Exception:
                    pass
                if exercise_type == "jumping_jack" and features is not None:
                    state = _pose_detect_states.setdefault(exercise_type, {})
                    try:
                        analysis = analyzer.analyze_frame(named_keypoints, state)
                    except Exception:
                        analysis = None

                results.append({
                    "keypoints": keypoints,
                    "features": features,
                    "analysis": analysis,
                })
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                results.append({"keypoints": None, "features": None, "error": str(e)[:200]})

        return {
            "exercise_type": exercise_type,
            "frames": results,
            "process_ms": round((time.perf_counter() - started_at) * 1000, 1),
        }

    @router.websocket("/pose")
    async def realtime_pose(websocket: WebSocket, exercise_type: str = Query("squat")):
        await websocket.accept()

        # Extract user_id from JWT token in query params (passed from frontend)
        token = websocket.query_params.get("token", "")
        user_id: int | None = None
        if token:
            payload = decode_access_token(token)
            if payload:
                username = payload.get("sub")
                if username:
                    from app.db.session import SessionLocal
                    db = SessionLocal()
                    try:
                        user = db.query(UserORM).filter(UserORM.username == username).first()
                        if user:
                            user_id = user.id
                    finally:
                        db.close()

        analyzer = get_analyzer(exercise_type)
        state: dict = {}
        running = False
        saved_session = None
        replay_frames: list[dict] = []

        def save_session_once():
            nonlocal saved_session
            if saved_session is not None:
                return saved_session

            summary = analyzer.get_session_summary()
            if summary["total_count"] <= 0 and not replay_frames:
                return None

            saved_session = session_service.create_session(
                exercise=summary["exercise"],
                duration_seconds=summary["duration_seconds"],
                total_count=summary["total_count"],
                valid_count=summary["valid_count"],
                error_count=summary["error_count"],
                average_score=summary["average_score"],
                user_id=user_id,
                pose_replay_frames=replay_frames,
                pose_replay_meta={
                    "source": "web_realtime",
                    "sample_interval_ms": 100,
                    "frame_count": len(replay_frames),
                },
            )
            return saved_session

        try:
            while True:
                payload = await websocket.receive_json()
                message_type = payload.get("type", "frame")

                if message_type == "start":
                    new_exercise = payload.get("exercise_type", exercise_type)
                    analyzer = get_analyzer(new_exercise)
                    analyzer.reset()
                    state = {}
                    saved_session = None
                    replay_frames = []
                    running = True
                    await websocket.send_json({
                        "type": "status",
                        "state": "running",
                        "exercise_type": new_exercise,
                        "core_metrics": [metric.to_dict() for metric in get_core_metrics(new_exercise)],
                    })
                    continue

                if message_type == "pause":
                    running = False
                    await websocket.send_json({
                        "type": "status", "state": "paused", "exercise_type": analyzer.exercise_type,
                    })
                    continue

                if message_type == "resume":
                    running = True
                    await websocket.send_json({
                        "type": "status", "state": "running", "exercise_type": analyzer.exercise_type,
                    })
                    continue

                if message_type == "finish":
                    running = False
                    session = save_session_once()
                    await websocket.send_json({
                        "type": "summary",
                        "state": "finished",
                        "session": session.to_dict() if session else analyzer.get_session_summary(),
                    })
                    continue

                if not running:
                    await websocket.send_json({
                        "type": "status", "state": "idle", "exercise_type": analyzer.exercise_type,
                    })
                    continue

                replay_keypoints = payload.get("replay_keypoints")
                if isinstance(replay_keypoints, list) and len(replay_keypoints) >= 33:
                    replay_frames.append({
                        "timestamp_ms": int(payload.get("timestamp_ms", len(replay_frames) * 100)),
                        "landmarks": replay_keypoints[:33],
                    })
                    if len(replay_frames) > 60000:
                        replay_frames = replay_frames[-60000:]

                keypoints = _parse_keypoints(payload.get("keypoints", {}))
                try:
                    result = analyzer.analyze_frame(keypoints, state)
                except ValueError as exc:
                    error_message = "关键点不足"
                    await websocket.send_json({
                        "type": "analysis",
                        "stage": "invalid",
                        "phase": "invalid",
                        "count": analyzer.count,
                        "valid_count": analyzer.valid_count,
                        "score": 0,
                        "issues": [error_message],
                        "errors": [error_message],
                        "feedback": [str(exc)],
                        "metrics": {},
                        "features": {},
                    })
                    continue
                result["metrics"] = result.get("features", {})
                result["type"] = "analysis"
                await websocket.send_json(result)

        except WebSocketDisconnect:
            save_session_once()
            return
