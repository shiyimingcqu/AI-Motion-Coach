from app.services.analysis.exercise_analyzer import ExerciseAnalyzer
from app.services.analysis.models import NormalizedKeypoint
from app.services.analysis.angle_feature_service import extract_squat_features
from app.services.analysis.template_service import TemplateService
from app.services.analysis.feedback_service import FeedbackService
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

# 初始化模板服务和反馈服务
template_service = TemplateService()
feedback_service = FeedbackService()


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
    @router.post("/analyze-frame")
    async def analyze_frame(request: dict):
        """
        分析单帧姿态，返回角度指标

        Request:
        {
            "action": "squat",
            "keypoints": {
                "left_shoulder": {"x": 0.4, "y": 0.3, "visibility": 0.99},
                ...
            }
        }

        Response:
        {
            "action": "squat",
            "metrics": {
                "knee_angle": 135.0,
                "hip_angle": 120.0,
                "trunk_angle": 18.0,
                "knee_symmetry_diff": 4.0
            }
        }
        """
        action = request.get("action", "squat")
        raw_keypoints = request.get("keypoints", {})

        if action != "squat":
            raise HTTPException(status_code=400, detail=f"暂不支持动作: {action}")

        try:
            keypoints = _parse_keypoints(raw_keypoints)
            metrics = extract_squat_features(keypoints)

            return {
                "action": action,
                "metrics": metrics
            }
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/score-action")
    async def score_action(request: dict):
        """
        根据标准模板对完整动作进行评分

        Request:
        {
            "action": "squat",
            "frames": [
                {
                    "knee_angle": 168,
                    "hip_angle": 172,
                    "trunk_angle": 8,
                    "knee_symmetry_diff": 2
                },
                ...
            ]
        }

        Response:
        {
            "action": "squat",
            "score": 82.5,
            "level": "good",
            "detail_scores": {
                "knee_angle": 76.2,
                "hip_angle": 80.5,
                "trunk_angle": 90.0,
                "knee_symmetry_diff": 88.0
            },
            "differences": {
                "knee_angle": 7.1,
                "hip_angle": 5.8,
                "trunk_angle": 3.0,
                "knee_symmetry_diff": 3.6
            },
            "errors": ["下蹲幅度略不足"],
            "suggestions": ["下蹲时继续降低重心，使膝关节弯曲更充分"]
        }
        """
        action = request.get("action", "squat")
        frames = request.get("frames", [])
        template_id = request.get("template_id")

        if action != "squat":
            raise HTTPException(status_code=400, detail=f"暂不支持动作: {action}")

        if not frames:
            raise HTTPException(status_code=400, detail="帧数据不能为空")

        try:
            # 根据模板评分
            if len(frames) < 2:
                raise HTTPException(status_code=400, detail="frames must contain at least 2 items")

            score_result = template_service.score_by_template(action, frames, template_id=template_id)
            template = template_service.load_template_by_id(template_id) if template_id else template_service.load_template(action)
            template_length = len(next(iter(template["template_sequence"].values()), []))

            # 生成反馈
            feedback = feedback_service.generate_template_feedback(score_result)

            return {
                "action": action,
                "template_id": template_id or "default",
                "is_partial": len(frames) < template_length,
                "score": score_result["score"],
                "level": score_result["level"],
                "detail_scores": score_result["detail_scores"],
                "differences": score_result["differences"],
                "errors": feedback["errors"],
                "suggestions": feedback["suggestions"]
            }
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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

                # 如果是深蹲动作，添加角度指标
                if analyzer.exercise == "squat":
                    try:
                        keypoints = _parse_keypoints(payload.get("keypoints", {}))
                        metrics = extract_squat_features(keypoints)
                        response["metrics"] = metrics
                    except ValueError:
                        # 如果无法计算指标，忽略错误
                        pass

                await websocket.send_json(response)
        except WebSocketDisconnect:
            save_session_once()
            return
