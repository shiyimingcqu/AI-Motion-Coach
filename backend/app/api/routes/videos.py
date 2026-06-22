from app.services.storage.local_storage import local_storage
from app.services.task.task_service import task_service

try:
    from fastapi import APIRouter, File, Form, UploadFile
except ModuleNotFoundError:
    APIRouter = None
    File = None
    Form = None
    UploadFile = None

router = APIRouter(prefix="/videos", tags=["videos"]) if APIRouter else None


if router:
    @router.post("/upload", status_code=201)
    async def upload_video(exercise: str = Form(...), file: UploadFile = File(...)):
        source_uri = await local_storage.save_upload(file)
        task = task_service.create_task(exercise=exercise, source_uri=source_uri)
        return {"file_uri": source_uri, "task": task.to_dict()}
