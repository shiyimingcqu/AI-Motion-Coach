from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect
except ModuleNotFoundError:
    APIRouter = None
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
    @router.websocket("/pose")
    async def realtime_pose(websocket: WebSocket):
        await websocket.accept()
        analyzer = ExerciseAnalyzer(exercise="squat")
        try:
            while True:
                payload = await websocket.receive_json()
                if payload.get("exercise") != analyzer.exercise:
                    analyzer = ExerciseAnalyzer(exercise=payload.get("exercise", "squat"))
                result = analyzer.analyze(_parse_keypoints(payload.get("keypoints", {})))
                await websocket.send_json(result.to_dict())
        except WebSocketDisconnect:
            return
