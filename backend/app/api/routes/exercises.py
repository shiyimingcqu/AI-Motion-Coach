from pathlib import Path
import shutil
from uuid import uuid4

try:
    from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
    from fastapi.responses import FileResponse
except ModuleNotFoundError:
    APIRouter = Depends = File = Form = UploadFile = HTTPException = None
    FileResponse = None

from app.api.deps import get_current_active_user, require_admin
from app.db.session import SessionLocal
from app.models.entities import ExerciseORM, ActiveTemplateORM
from app.services.exercise.registry import list_exercises
from app.services.analysis.analyzers.registry import ANALYZER_REGISTRY
from app.services.analysis.template_builder_service import template_builder_service
from app.services.analysis.template_service import get_active_template_id, refresh_active_templates
from app.services.analysis.template_service import TemplateService
from app.core.config import settings

router = APIRouter(tags=["exercises"]) if APIRouter else None


if router:
    template_reader = TemplateService()

    @router.get("/exercises")
    def get_exercises(
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """获取动作库列表（从数据库读取，含详细配置）"""
        if SessionLocal is None:
            return {"items": [e.to_dict() for e in list_exercises()]}
        db = SessionLocal()
        try:
            items = db.query(ExerciseORM).order_by(ExerciseORM.id).all()
            return {"items": [e.to_dict() for e in items]}
        finally:
            db.close()

    @router.get("/exercises/simple")
    def list_exercise_definitions(
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """获取精简的动作定义列表（分析器支持的动作，供训练使用）"""
        return {"items": [exercise.to_dict() for exercise in list_exercises()]}

    @router.post("/exercises", status_code=201)
    def create_exercise(
        data: dict,
        current_user=Depends(require_admin) if require_admin else None,
    ):
        """管理员新增动作"""
        if SessionLocal is None:
            raise HTTPException(status_code=500, detail="DB unavailable")
        db = SessionLocal()
        try:
            existing = db.query(ExerciseORM).filter(ExerciseORM.key == data.get("key")).first()
            if existing:
                raise HTTPException(status_code=400, detail="动作 key 已存在")
            errors_val = data.get("errors", "")
            if isinstance(errors_val, list):
                errors_val = ",".join(str(e).strip() for e in errors_val if str(e).strip())
            modes_val = data.get("modes", "摄像头实时检测,视频上传分析")
            if isinstance(modes_val, list):
                modes_val = ",".join(str(m).strip() for m in modes_val if str(m).strip())
            ex = ExerciseORM(
                key=data.get("key"),
                name=data.get("name", data.get("key")),
                category=data.get("category", "通用"),
                level=data.get("level", "中级"),
                duration=data.get("duration", "10 分钟"),
                description=data.get("description", ""),
                modes=modes_val,
                errors=errors_val,
                accent=data.get("accent", "#3b82f6"),
            )
            db.add(ex)
            db.commit()
            db.refresh(ex)
            return ex.to_dict()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.put("/exercises/{exercise_key}")
    def update_exercise(
        exercise_key: str,
        data: dict,
        current_user=Depends(require_admin) if require_admin else None,
    ):
        """管理员更新动作配置"""
        if SessionLocal is None:
            raise HTTPException(status_code=500, detail="DB unavailable")
        db = SessionLocal()
        try:
            ex = db.query(ExerciseORM).filter(ExerciseORM.key == exercise_key).first()
            if not ex:
                raise HTTPException(status_code=404, detail="动作不存在")
            list_fields = {"modes", "errors"}
            for field in ("name", "category", "level", "duration", "description", "modes", "errors", "accent", "is_active"):
                if field in data:
                    value = data[field]
                    # 前端发送的是数组，后端存储为逗号分隔字符串
                    if field in list_fields and isinstance(value, list):
                        value = ",".join(str(v).strip() for v in value if str(v).strip())
                    setattr(ex, field, value)
            from datetime import datetime, timezone
            ex.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(ex)
            return ex.to_dict()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.delete("/exercises/{exercise_key}")
    def delete_exercise(
        exercise_key: str,
        current_user=Depends(require_admin) if require_admin else None,
    ):
        """管理员删除动作"""
        if SessionLocal is None:
            raise HTTPException(status_code=500, detail="DB unavailable")
        db = SessionLocal()
        try:
            ex = db.query(ExerciseORM).filter(ExerciseORM.key == exercise_key).first()
            if not ex:
                raise HTTPException(status_code=404, detail="动作不存在")
            db.delete(ex)
            db.commit()
            return {"message": "Exercise deleted", "key": exercise_key}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @router.get("/exercises/{exercise}/templates")
    def get_templates(
        exercise: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        """
        获取指定动作的所有模板列表（包含启用状态）
        """
        if exercise not in ANALYZER_REGISTRY:
            raise HTTPException(status_code=400, detail=f"不支持的动作类型: {exercise}")

        templates = template_builder_service.list_templates(exercise)
        active_id = get_active_template_id(exercise)

        for t in templates:
            t["is_enabled"] = (t["template_id"] == active_id)

        return {"items": templates}

    @router.get("/exercises/{exercise}/templates/active")
    def get_active_template(
        exercise: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        if exercise not in ANALYZER_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Unsupported exercise type: {exercise}")
        active_id = get_active_template_id(exercise)
        if not active_id:
            return {"template": None}
        try:
            template = template_reader.load_template_by_id(active_id)
        except (FileNotFoundError, ValueError):
            return {"template": None}

        video_uri = template.get("video_uri")
        pose_replay_frames = template.get("pose_replay_frames") or []
        return {
            "template": {
                "template_id": active_id,
                "action": template.get("action"),
                "name": template.get("name") or active_id,
                "view": template.get("view") or "default",
                "version": template.get("version"),
                "valid_frames": template.get("source", {}).get("valid_frames", 0),
                "source": template.get("source", {}).get("type", "template"),
                "is_enabled": True,
                "has_video": bool(video_uri and Path(video_uri).exists()),
                "has_pose_replay": bool(pose_replay_frames),
            }
        }

    @router.post("/exercises/{exercise}/templates/from-video", status_code=201)
    def create_template_from_video(
        exercise: str,
        video: UploadFile | None = File(None),
        file: UploadFile | None = File(None),
        name: str | None = Form(None),
        view: str = Form("side"),
        version: str = Form("v1"),
        current_user=Depends(require_admin) if require_admin else None,
    ):
        """
        从视频生成标准动作模板（管理员专用）
        """
        if exercise not in ANALYZER_REGISTRY:
            raise HTTPException(status_code=400, detail=f"不支持的动作类型: {exercise}")

        video_file = video or file
        if video_file is None:
            raise HTTPException(status_code=400, detail="请上传标准动作视频")

        valid_views = ["side", "front", "diagonal"]
        if view not in valid_views:
            raise HTTPException(status_code=400, detail=f"无效的拍摄角度: {view}，可选值: {valid_views}")

        temp_dir = Path(settings.storage_root) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"template_video_{uuid4().hex[:8]}.mp4"
        template_id = f"{exercise}_template_{view}_{version}"
        video_dir = Path(settings.storage_root) / "template_videos"
        video_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(video_file.filename or "").suffix or ".mp4"
        video_path = video_dir / f"{template_id}{suffix}"

        try:
            with open(temp_path, 'wb') as f:
                f.write(video_file.file.read())
            shutil.copyfile(temp_path, video_path)

            result = template_builder_service.build_from_video(
                video_path=str(temp_path),
                action=exercise,
                view=view,
                name=name,
                version=version,
                video_uri=str(video_path).replace("\\", "/"),
            )

            for analyzer in ANALYZER_REGISTRY.values():
                template_service = getattr(analyzer, "template_service", None)
                if template_service is not None:
                    template_service.templates.clear()
                if hasattr(analyzer, "_template_reference_cache"):
                    analyzer._template_reference_cache = None
            template_reader.templates.clear()

            if SessionLocal is not None:
                db = SessionLocal()
                try:
                    refresh_active_templates(db)
                finally:
                    db.close()

            return {
                "status": "success",
                "message": "模板生成成功",
                **result
            }

        except ValueError as e:
            video_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            video_path.unlink(missing_ok=True)
            raise HTTPException(status_code=500, detail=f"模板生成失败: {str(e)}")
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    @router.get("/templates/{template_id}/video")
    def stream_template_video(
        template_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        try:
            template = template_reader.load_template_by_id(template_id)
        except (FileNotFoundError, ValueError):
            raise HTTPException(status_code=404, detail="Template not found")
        video_uri = template.get("video_uri")
        if not video_uri:
            raise HTTPException(status_code=404, detail="Template video not found")
        video_path = Path(video_uri)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Template video file not found")
        return FileResponse(str(video_path), media_type="video/mp4")

    @router.get("/templates/{template_id}/replay")
    def get_template_replay(
        template_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        try:
            template = template_reader.load_template_by_id(template_id)
        except (FileNotFoundError, ValueError):
            raise HTTPException(status_code=404, detail="Template not found")
        frames = template.get("pose_replay_frames") or []
        normalized = []
        for index, frame in enumerate(frames):
            landmarks = frame.get("landmarks") if isinstance(frame, dict) else None
            if not isinstance(landmarks, list) or len(landmarks) < 33:
                continue
            normalized.append({
                "timestamp_ms": int(frame.get("timestamp_ms", index * 100)),
                "landmarks": landmarks[:33],
            })
        return {
            "template_id": Path(template_id).stem,
            "exercise": template.get("action"),
            "has_replay": bool(normalized),
            "frames": normalized,
            "meta": {
                "source": "template_video",
                "frame_count": len(normalized),
                "sample_interval_ms": 100,
            },
        }
