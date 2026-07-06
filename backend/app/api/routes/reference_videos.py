from pathlib import Path

from app.api.deps import get_current_active_user, get_db, require_admin
from app.models.entities import ReferenceVideoORM
from app.services.storage.local_storage import local_storage

try:
    from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
    from fastapi.responses import FileResponse
    from sqlalchemy.orm import Session
except ModuleNotFoundError:
    APIRouter = Depends = None
    File = Form = UploadFile = HTTPException = None
    FileResponse = None
    Session = None

router = APIRouter(prefix="/reference-videos", tags=["reference_videos"]) if APIRouter else None

if router:
    @router.get("")
    def list_reference_videos(db: Session = Depends(get_db)):
        """获取所有启用的标准视频（所有登录用户可访问）"""
        items = (
            db.query(ReferenceVideoORM)
            .filter(ReferenceVideoORM.is_active == True)
            .order_by(ReferenceVideoORM.created_at.desc())
            .all()
        )
        return {"items": [v.to_dict() for v in items]}

    @router.get("/all")
    def list_all_reference_videos(
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        """管理员获取所有标准视频（含停用）"""
        items = (
            db.query(ReferenceVideoORM)
            .order_by(ReferenceVideoORM.created_at.desc())
            .all()
        )
        return {"items": [v.to_dict() for v in items]}

    @router.post("", status_code=201)
    async def upload_reference_video(
        title: str = Form(...),
        exercise: str = Form("squat"),
        camera_view: str = Form("front"),
        description: str = Form(""),
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_user=Depends(require_admin),
    ):
        """管理员上传标准视频"""
        file_uri = await local_storage.save_upload(file)
        video = ReferenceVideoORM(
            title=title,
            exercise=exercise,
            camera_view=camera_view,
            description=description,
            file_uri=file_uri,
            uploaded_by=current_user.id if current_user else None,
            is_active=True,
        )
        db.add(video)
        try:
            db.commit()
            db.refresh(video)
        except Exception:
            db.rollback()
            raise
        return {"video": video.to_dict()}

    @router.patch("/{video_id}")
    def update_reference_video(
        video_id: int,
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        """管理员切换标准视频启用/停用状态"""
        video = db.query(ReferenceVideoORM).filter(ReferenceVideoORM.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="标准视频不存在")
        video.is_active = not video.is_active
        try:
            db.commit()
            db.refresh(video)
        except Exception:
            db.rollback()
            raise
        return {"video": video.to_dict()}

    @router.delete("/{video_id}", status_code=204)
    def delete_reference_video(
        video_id: int,
        db: Session = Depends(get_db),
        _=Depends(require_admin),
    ):
        """管理员删除标准视频"""
        video = db.query(ReferenceVideoORM).filter(ReferenceVideoORM.id == video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail="标准视频不存在")
        db.delete(video)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        return None

    @router.get("/{video_id}/stream")
    def stream_reference_video(
        video_id: int,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user),
    ):
        """流式返回标准视频文件"""
        video = db.query(ReferenceVideoORM).filter(
            ReferenceVideoORM.id == video_id,
            ReferenceVideoORM.is_active == True,
        ).first()
        if not video:
            raise HTTPException(status_code=404, detail="标准视频不存在")
        file_path = Path(video.file_uri)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="视频文件不存在")
        return FileResponse(str(file_path), media_type="video/mp4")
