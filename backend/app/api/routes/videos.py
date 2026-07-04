from app.api.deps import get_current_active_user
from app.services.storage.local_storage import local_storage
from app.services.task.task_service import task_service
from app.services.video.video_analysis_service import video_analysis_service

try:
    from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
except ModuleNotFoundError:
    APIRouter = Depends = HTTPException = None
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
        if not file.filename:
            raise HTTPException(status_code=400, detail="请选择视频文件")

        user_id = current_user.id if current_user else None

        try:
            source_uri = await local_storage.save_upload(file)
            output_uri, session_record = video_analysis_service.analyze_video(
                source_uri,
                exercise,
                user_id=user_id,
            )
            task = task_service.create_task(
                exercise=exercise,
                source_uri=source_uri,
                status="success",
                output_uri=output_uri,
            )
            response = {"file_uri": source_uri, "task": task}
            if session_record is not None:
                response["session_id"] = session_record.session_id
                response["session"] = session_record.to_dict()
            return response
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"视频分析失败，请确认视频格式正确且后端依赖已安装: {exc}",
            ) from exc
