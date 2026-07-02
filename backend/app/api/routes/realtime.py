"""Realtime analysis WebSocket and HTTP endpoints — multi-exercise support."""

from app.api.deps import get_current_active_user
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.entities import UserORM
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.analyzers.registry import get_analyzer, ANALYZER_REGISTRY
from app.services.storage.local_storage import local_storage
from app.services.session.session_service import session_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, Query
except ModuleNotFoundError:
    APIRouter = None
    File = Form = HTTPException = UploadFile = WebSocket = WebSocketDisconnect = Query = None

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
        max_frames: int = Form(120),
        file: UploadFile = File(...),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        source_uri = await local_storage.save_upload(file)
        try:
            return video_analysis_service.run_realtime_video_test(
                source_uri=source_uri,
                exercise=exercise,
                max_frames=max_frames,
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

        def save_session_once():
            nonlocal saved_session
            if saved_session is not None:
                return saved_session

            summary = analyzer.get_session_summary()
            if summary["total_count"] <= 0:
                return None

            saved_session = session_service.create_session(
                exercise=summary["exercise"],
                duration_seconds=summary["duration_seconds"],
                total_count=summary["total_count"],
                valid_count=summary["valid_count"],
                error_count=summary["error_count"],
                average_score=summary["average_score"],
                user_id=user_id,
            )
            return saved_session

        try:
            while True:
                payload = await websocket.receive_json()
                message_type = payload.get("type", "frame")

                if message_type == "start":
                    new_exercise = payload.get("exercise_type", exercise_type)
                    analyzer = get_analyzer(new_exercise)
                    state = {}
                    saved_session = None
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

                keypoints = _parse_keypoints(payload.get("keypoints", {}))
                result = analyzer.analyze_frame(keypoints, state)
                result["metrics"] = result.get("features", {})
                result["type"] = "analysis"
                await websocket.send_json(result)

        except WebSocketDisconnect:
            save_session_once()
            return
