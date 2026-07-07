from app.api.deps import get_current_active_user
from app.services.storage.local_storage import local_storage
from app.services.task.task_service import task_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
except ModuleNotFoundError:
    APIRouter = Depends = None
    File = None
    Form = None
    HTTPException = None
    UploadFile = None

router = APIRouter(prefix="/videos", tags=["videos"]) if APIRouter else None


if router:
    @router.post("/upload", status_code=201)
    async def upload_video(
        exercise: str = Form(...),
        file: UploadFile = File(...),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        source_uri = await local_storage.save_upload(file)
        user_id = current_user.id if current_user else None
        try:
            analysis_result = video_analysis_service.analyze_video(
                source_uri, exercise, user_id=user_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        task = task_service.create_task(
            exercise=exercise,
            source_uri=source_uri,
            status="success",
            output_uri=analysis_result["output_uri"],
        )
        return {
            "file_uri": source_uri,
            "task": task,
            "analysis": analysis_result,
            "session_id": analysis_result.get("session_id"),
        }
