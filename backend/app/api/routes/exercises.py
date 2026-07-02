from pathlib import Path
from uuid import uuid4

try:
    from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
except ModuleNotFoundError:
    APIRouter = Depends = File = UploadFile = HTTPException = None

from app.api.deps import get_current_active_user, require_admin
from app.db.session import SessionLocal
from app.models.entities import ExerciseORM
from app.services.exercise.registry import list_exercises
from app.services.analysis.analyzers.registry import ANALYZER_REGISTRY
from app.services.analysis.template_builder_service import template_builder_service
from app.core.config import settings

router = APIRouter(tags=["exercises"]) if APIRouter else None


if router:
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
        获取指定动作的所有模板列表
        """
        if exercise not in ANALYZER_REGISTRY:
            raise HTTPException(status_code=400, detail=f"不支持的动作类型: {exercise}")

        templates = template_builder_service.list_templates(exercise)
        return {"items": templates}

    @router.post("/exercises/{exercise}/templates/from-video", status_code=201)
    def create_template_from_video(
        exercise: str,
        video: UploadFile = File(...),
        name: str = None,
        view: str = "side",
        version: str = "v1",
        current_user=Depends(require_admin) if require_admin else None,
    ):
        """
        从视频生成标准动作模板（管理员专用）
        """
        if exercise not in ANALYZER_REGISTRY:
            raise HTTPException(status_code=400, detail=f"不支持的动作类型: {exercise}")

        valid_views = ["side", "front", "diagonal"]
        if view not in valid_views:
            raise HTTPException(status_code=400, detail=f"无效的拍摄角度: {view}，可选值: {valid_views}")

        temp_dir = Path(settings.storage_root) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"template_video_{uuid4().hex[:8]}.mp4"

        try:
            with open(temp_path, 'wb') as f:
                f.write(video.file.read())

            result = template_builder_service.build_from_video(
                video_path=str(temp_path),
                action=exercise,
                view=view,
                name=name,
                version=version
            )

            return {
                "status": "success",
                "message": "模板生成成功",
                **result
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"模板生成失败: {str(e)}")
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
