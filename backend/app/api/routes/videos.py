from typing import Optional

from app.api.deps import get_current_active_user
from app.services.storage.local_storage import local_storage
from app.services.task.task_service import task_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Depends, File, Form, UploadFile
    from fastapi.concurrency import run_in_threadpool
except ModuleNotFoundError:
    APIRouter = Depends = None
    File = None
    Form = None
    UploadFile = None
    run_in_threadpool = None

router = APIRouter(prefix="/videos", tags=["videos"]) if APIRouter else None


if router:
    @router.post("/upload", status_code=201)
    async def upload_video(
        exercise: str = Form(...),
        camera_view: str = Form("front"),
        session_id: Optional[str] = Form(None),
        file: UploadFile = File(...),
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        source_uri = await local_storage.save_upload(file)
        uid = current_user.id if current_user else None
        try:
            result = await run_in_threadpool(
                video_analysis_service.analyze_video,
                source_uri, exercise, uid,
            )
            task = task_service.create_task(
                exercise=exercise,
                source_uri=source_uri,
                status="success",
                output_uri=result.get("output_uri", source_uri),
                camera_view=camera_view,
                user_id=uid,
            )
        except Exception as e:
            task = task_service.create_task(
                exercise=exercise,
                source_uri=source_uri,
                status="failed",
                error_message=str(e),
                camera_view=camera_view,
                user_id=uid,
            )
            return {"file_uri": source_uri, "task": task, "error": str(e)}
        return {"file_uri": source_uri, "task": task}
