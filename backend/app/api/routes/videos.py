from app.api.deps import get_current_active_user
from app.services.storage.local_storage import local_storage
from app.services.task.task_service import task_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Depends, File, Form, UploadFile
except ModuleNotFoundError:
    APIRouter = Depends = None
    File = None
    Form = None
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
        output_uri = video_analysis_service.analyze_video(source_uri, exercise)
        task = task_service.create_task(
            exercise=exercise,
            source_uri=source_uri,
            status="success",
            output_uri=output_uri,
        )
        return {"file_uri": source_uri, "task": task.to_dict()}
