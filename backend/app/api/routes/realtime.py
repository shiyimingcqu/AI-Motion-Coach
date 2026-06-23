from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint
from app.services.storage.local_storage import local_storage
from app.services.session.session_service import session_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
except ModuleNotFoundError:
    APIRouter = None
    File = None
    Form = None
    HTTPException = Exception
    UploadFile = None
    WebSocket = None
    WebSocketDisconnect = Exception

router = APIRouter(prefix="/realtime", tags=["realtime"]) if APIRouter else None


def _parse_keypoints(raw_keypoints):
    return {
        name: NormalizedKeypoint(
            x=value["x"],
            y=value["y"],
            visibility=value.get("visibility", 1.0),
        )
        for name, value in raw_keypoints.items()
    }


if router:
    @router.post("/video-test", status_code=201)
    async def realtime_video_test(
        exercise: str = Form("squat"),
        max_frames: int = Form(120),
        file: UploadFile = File(...),
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

    @router.websocket("/pose")
    async def realtime_pose(websocket: WebSocket):
        await websocket.accept()
        analyzer = ExerciseAnalyzer(exercise="squat")
        running = False
        saved_session = None

        def save_session_once():
            nonlocal saved_session
            if saved_session is not None:
                return saved_session

            session_summary = analyzer.get_session_summary()
            if session_summary["total_count"] <= 0:
                return None

            saved_session = session_service.create_session(
                exercise=session_summary["exercise"],
                duration_seconds=session_summary["duration_seconds"],
                total_count=session_summary["total_count"],
                valid_count=session_summary["valid_count"],
                error_count=session_summary["error_count"],
                average_score=session_summary["average_score"],
            )
            return saved_session

        try:
            while True:
                payload = await websocket.receive_json()
                message_type = payload.get("type", "frame")

                if message_type == "start":
                    exercise = payload.get("exercise", analyzer.exercise)
                    analyzer = ExerciseAnalyzer(exercise=exercise)
                    saved_session = None
                    running = True
                    await websocket.send_json({"type": "status", "state": "running", "exercise": exercise})
                    continue

                if message_type == "pause":
                    running = False
                    await websocket.send_json({"type": "status", "state": "paused", "exercise": analyzer.exercise})
                    continue

                if message_type == "resume":
                    running = True
                    await websocket.send_json({"type": "status", "state": "running", "exercise": analyzer.exercise})
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

                if payload.get("exercise") != analyzer.exercise:
                    analyzer = ExerciseAnalyzer(exercise=payload.get("exercise", "squat"))
                    saved_session = None

                if not running:
                    await websocket.send_json({"type": "status", "state": "idle", "exercise": analyzer.exercise})
                    continue

                result = analyzer.analyze(_parse_keypoints(payload.get("keypoints", {})))
                response = result.to_dict()
                response["type"] = "analysis"
                await websocket.send_json(response)
        except WebSocketDisconnect:
            save_session_once()
            return
