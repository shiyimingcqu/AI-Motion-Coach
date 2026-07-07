"""Realtime analysis WebSocket and HTTP endpoints — multi-exercise support."""

import base64
import json
import logging

import numpy as np

from app.api.deps import get_current_active_user
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import UserORM, SessionORM
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.analyzers.registry import get_analyzer, ANALYZER_REGISTRY
from app.services.pose.mediapipe_engine import MediaPipePoseEngine
from app.services.storage.local_storage import local_storage
from app.services.session.session_service import session_service
from app.services.video.video_analysis_service import video_analysis_service

logger = logging.getLogger(__name__)
_pose_engine = None


def _get_pose_engine():
    global _pose_engine
    if _pose_engine is None:
        _pose_engine = MediaPipePoseEngine()
    return _pose_engine


def _landmarks_dict_to_array(landmarks_dict: dict) -> list:
    """Convert MediaPipe engine output {idx: {x,y,z,visibility}} to array of 33 elements."""
    arr = [None] * 33
    for idx_str, kp in landmarks_dict.items():
        idx = int(idx_str)
        if 0 <= idx < 33:
            arr[idx] = {"x": kp["x"], "y": kp["y"], "z": kp.get("z", 0.0), "visibility": kp.get("visibility", 1.0)}
    return arr


def _decode_base64_image(base64_str: str):
    """Decode base64 image string to BGR numpy array."""
    import cv2
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",", 1)[1]
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return frame
    except Exception as exc:
        logger.warning("Failed to decode base64 image: %s", exc)
        return None

try:
    from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect, Query
except ModuleNotFoundError:
    APIRouter = None
    File = Form = HTTPException = Request = UploadFile = WebSocket = WebSocketDisconnect = Query = None

router = APIRouter(prefix="/realtime", tags=["realtime"]) if APIRouter else None


def _parse_keypoints(raw_keypoints: dict) -> dict[str, NormalizedKeypoint]:
    return {
        name: NormalizedKeypoint(
            x=value["x"],
            y=value["y"],
            visibility=value.get("visibility", 1.0),
        )
        for name, value in raw_keypoints.items()
    }


if router:
    @router.post("/pose-detect")
    async def pose_detect(request: Request):
        """
        Detect pose keypoints from base64-encoded image frames.
        Request body:
        {
            "exercise_type": "squat",
            "frames": [{"image": "<base64 JPEG>"}],
            "reset_state": false
        }
        Response:
        {
            "frames": [{
                "keypoints": [{"x": 0.5, "y": 0.6, "visibility": 0.9}, ...],
                "features": {...},
                "analysis": {...}
            }]
        }
        """
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        exercise_type = body.get("exercise_type", "squat")
        frames = body.get("frames", [])
        reset_state = body.get("reset_state", False)

        if not frames or not isinstance(frames, list):
            raise HTTPException(status_code=400, detail="frames must be a non-empty list")

        engine = _get_pose_engine()
        results = []

        for frame_item in frames[:5]:  # limit to 5 frames per request
            img_b64 = frame_item.get("image", "")
            if not img_b64:
                results.append({"keypoints": [None] * 33})
                continue

            frame = _decode_base64_image(img_b64)
            if frame is None:
                results.append({"keypoints": [None] * 33})
                continue

            try:
                landmarks_dict = engine.infer(frame)
            except FileNotFoundError as exc:
                raise HTTPException(status_code=500, detail=str(exc))
            except Exception as exc:
                logger.warning("Pose inference failed: %s", exc)
                results.append({"keypoints": [None] * 33})
                continue

            keypoints_array = _landmarks_dict_to_array(landmarks_dict)

            # Optionally run analysis if we have enough visible keypoints
            analysis = None
            try:
                analyzer = get_analyzer(exercise_type)
                named_kps = {}
                for i, kp in enumerate(keypoints_array):
                    if kp and kp.get("visibility", 0) > 0.3:
                        named_kps[str(i)] = NormalizedKeypoint(
                            x=kp["x"], y=kp["y"], visibility=kp["visibility"]
                        )
                if named_kps:
                    features = analyzer.extract_features(named_kps)
                    analysis = {"features": features}
            except Exception:
                pass

            result = {"keypoints": keypoints_array}
            if analysis:
                result["analysis"] = analysis.get("features")
            results.append(result)

        return {"frames": results}

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
        max_frames: int = Form(240),
        persist_session: str = Form("false"),
        file: UploadFile = File(...),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        source_uri = await local_storage.save_upload(file)
        try:
            user_id = current_user.id if current_user else None
            should_persist = str(persist_session).lower() in {"1", "true", "yes", "on"}
            return video_analysis_service.run_realtime_video_test(
                source_uri=source_uri,
                exercise=exercise,
                max_frames=max_frames,
                persist_session=should_persist,
                user_id=user_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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
        error_snapshots: list[dict] = []
        last_frame_score = 100.0
        last_error_capture_ms = -100000
        ERROR_CAPTURE_THRESHOLD = 80
        ERROR_CAPTURE_COOLDOWN_MS = 2500

        def save_session_once():
            nonlocal saved_session
            if saved_session is not None:
                return saved_session

            summary = analyzer.get_session_summary()
            if summary["total_count"] <= 0 and not replay_frames:
                return None

            avg_score = float(summary["average_score"])
            if replay_frames and avg_score < ERROR_CAPTURE_THRESHOLD:
                has_landmark_snap = any(s.get("landmarks") for s in error_snapshots)
                pick_frame = (
                    min(
                        replay_frames,
                        key=lambda f: float(
                            next(
                                (s.get("score") for s in error_snapshots if s.get("timestamp_ms") == f.get("timestamp_ms")),
                                avg_score,
                            )
                        ),
                    )
                    if error_snapshots
                    else replay_frames[len(replay_frames) // 2]
                )
                lm = pick_frame.get("landmarks") if isinstance(pick_frame, dict) else None
                ts = int(pick_frame.get("timestamp_ms", 0)) if isinstance(pick_frame, dict) else 0
                if lm and not has_landmark_snap:
                    error_snapshots.append({
                        "timestamp_ms": ts,
                        "score": avg_score,
                        "landmarks": lm,
                        "errors": ["本次训练平均分低于阈值，建议对照反馈重点改进"],
                        "capture_type": "session_summary",
                    })
                elif lm and not any(s.get("capture_type") == "session_summary" for s in error_snapshots):
                    error_snapshots.append({
                        "timestamp_ms": ts,
                        "score": avg_score,
                        "landmarks": lm,
                        "errors": ["本次训练平均分低于阈值，建议对照反馈重点改进"],
                        "capture_type": "session_summary",
                    })

            replay_meta = {
                "source": "web_realtime",
                "sample_interval_ms": 100,
                "frame_count": len(replay_frames),
                "error_snapshots": error_snapshots[:30],
            }
            from app.services.report.error_frame_service import ensure_meta_error_snapshots
            replay_meta = ensure_meta_error_snapshots(
                replay_meta,
                replay_frames,
                avg_score,
            )

            # 即使未计次也保存 session，便于跳转反馈页展示分析建议
            # 生成 rep_segments（按单次动作筛选回放）
            rep_segments_payload: list[dict] = []
            if hasattr(analyzer, "rep_segments"):
                for seg in analyzer.rep_segments:
                    si = seg.get("start_frame_index", 0)
                    ei = seg.get("end_frame_index", 0)
                    st = replay_frames[si]["timestamp_ms"] if si < len(replay_frames) else 0
                    et = replay_frames[ei]["timestamp_ms"] if ei < len(replay_frames) else 0
                    rep_segments_payload.append({
                        "rep_index": seg["rep_index"],
                        "start_frame_index": si,
                        "end_frame_index": ei,
                        "start_timestamp_ms": st,
                        "end_timestamp_ms": et,
                        "score": seg.get("score", 0),
                        "issues": seg.get("issues", []),
                    })
            rep_nodes_payload: list[dict] = []
            if hasattr(analyzer, "rep_nodes"):
                for node in analyzer.rep_nodes:
                    frame_index = int(node.get("frame_index", 0))
                    timestamp_ms = (
                        replay_frames[frame_index]["timestamp_ms"]
                        if 0 <= frame_index < len(replay_frames)
                        else 0
                    )
                    rep_nodes_payload.append({
                        "rep_index": node.get("rep_index"),
                        "frame_index": frame_index,
                        "timestamp_ms": timestamp_ms,
                        "start_frame_index": int(node.get("start_frame_index", frame_index)),
                        "score": node.get("score", 0),
                        "issues": node.get("issues", []),
                    })

            replay_meta["rep_segments"] = rep_segments_payload
            replay_meta["rep_nodes"] = rep_nodes_payload

            saved_session = session_service.create_session(
                exercise=summary["exercise"],
                duration_seconds=summary["duration_seconds"],
                total_count=summary["total_count"],
                valid_count=summary["valid_count"],
                error_count=summary["error_count"],
                average_score=summary["average_score"],
                user_id=user_id,
                pose_replay_frames=replay_frames,
                pose_replay_meta=replay_meta,
            )

            # 保存反馈摘要（AI 建议后台异步生成，不阻塞跳转评估页）
            try:
                from app.services.analysis.unified_feedback_service import (
                    build_unified_feedback_from_analyzer,
                    unified_feedback_service,
                )
                from app.services.session.feedback_persistence import (
                    build_feedback_data,
                    load_session_orm,
                    save_session_feedback_summary,
                )

                unified_feedback = build_unified_feedback_from_analyzer(analyzer)
                formatted = unified_feedback_service.format_for_ai(unified_feedback)
                feedback_data = build_feedback_data(unified_feedback, formatted)
                save_session_feedback_summary(
                    saved_session.session_id,
                    feedback_data,
                    generate_ai_async=True,
                    exercise=summary["exercise"],
                )
                refreshed = load_session_orm(saved_session.session_id)
                if refreshed is not None:
                    saved_session = refreshed
            except Exception:
                pass  # 反馈保存失败不影响主流程

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
                    error_snapshots = []
                    last_frame_score = 100.0
                    last_error_capture_ms = -100000
                    running = True
                    await websocket.send_json({
                        "type": "status", "state": "running", "exercise_type": new_exercise,
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
                frame_index = len(replay_frames) - 1 if replay_frames else 0
                try:
                    result = analyzer.analyze_frame(
                        keypoints, state,
                        frame_index=frame_index,
                    )
                except ValueError as exc:
                    await websocket.send_json({
                        "type": "analysis",
                        "exercise_type": analyzer.exercise_type,
                        "phase": getattr(analyzer, "stage", "ready"),
                        "stage": getattr(analyzer, "stage", "ready"),
                        "count": analyzer.count,
                        "valid_count": analyzer.valid_count,
                        "score": 0,
                        "issues": [],
                        "errors": [],
                        "feedback": [],
                        "features": {},
                        "metrics": {},
                        "detail_scores": {},
                        "skip_reason": str(exc),
                    })
                    continue
                except Exception as exc:
                    logger.warning("Realtime frame analysis failed (%s): %s", analyzer.exercise_type, exc)
                    await websocket.send_json({
                        "type": "analysis",
                        "exercise_type": analyzer.exercise_type,
                        "phase": getattr(analyzer, "stage", "ready"),
                        "stage": getattr(analyzer, "stage", "ready"),
                        "count": analyzer.count,
                        "valid_count": analyzer.valid_count,
                        "score": 0,
                        "issues": [],
                        "errors": [],
                        "feedback": [],
                        "features": {},
                        "metrics": {},
                        "detail_scores": {},
                        "skip_reason": "analysis_error",
                    })
                    continue

                result["metrics"] = result.get("features", {})
                result["stage"] = result.get("stage") or result.get("phase", "")
                result["errors"] = result.get("errors") or result.get("issues", [])
                result["type"] = "analysis"

                frame_score = result.get("score", 0)
                frame_errors = result.get("errors") or []
                if isinstance(replay_keypoints, list) and len(replay_keypoints) >= 33:
                    ts = int(payload.get("timestamp_ms", len(replay_frames) * 100))
                    score_f = float(frame_score) if isinstance(frame_score, (int, float)) else 100.0
                    crossed_below = last_frame_score >= ERROR_CAPTURE_THRESHOLD and score_f < ERROR_CAPTURE_THRESHOLD
                    has_errors = bool(frame_errors)
                    cooldown_ok = ts - last_error_capture_ms >= ERROR_CAPTURE_COOLDOWN_MS

                    if score_f < ERROR_CAPTURE_THRESHOLD and cooldown_ok:
                        should_capture = crossed_below or has_errors or len(error_snapshots) == 0
                        if should_capture:
                            error_snapshots.append({
                                "timestamp_ms": ts,
                                "score": score_f,
                                "landmarks": replay_keypoints[:33],
                                "errors": frame_errors[:5] if frame_errors else [f"实时评分 {score_f:.0f} 分低于 {ERROR_CAPTURE_THRESHOLD} 分阈值"],
                                "metrics": result.get("features") or result.get("metrics") or {},
                                "capture_type": "threshold_cross",
                            })
                            last_error_capture_ms = ts
                            if len(error_snapshots) > 30:
                                error_snapshots[:] = error_snapshots[-30:]

                    last_frame_score = score_f

                await websocket.send_json(result)

        except WebSocketDisconnect:
            save_session_once()
            return
