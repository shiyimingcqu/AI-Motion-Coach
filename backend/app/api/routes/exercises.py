from pathlib import Path
from uuid import uuid4

try:
    from fastapi import APIRouter, File, UploadFile, HTTPException
except ModuleNotFoundError:
    APIRouter = File = UploadFile = HTTPException = None

from app.services.exercise.registry import list_exercises
from app.services.analysis.template_builder_service import template_builder_service
from app.core.config import settings

router = APIRouter(tags=["exercises"]) if APIRouter else None


if router:
    @router.get("/exercises")
    def get_exercises():
        return {"items": [exercise.to_dict() for exercise in list_exercises()]}

    @router.get("/exercises/{exercise}/templates")
    def get_templates(exercise: str):
        """
        获取指定动作的所有模板列表

        Args:
            exercise: 动作类型（如 "squat"）

        Returns:
            模板列表
        """
        templates = template_builder_service.list_templates(exercise)
        return {"items": templates}

    @router.post("/exercises/{exercise}/templates/from-video", status_code=201)
    def create_template_from_video(
        exercise: str,
        video: UploadFile = File(...),
        name: str = None,
        view: str = "side",
        version: str = "v1"
    ):
        """
        从视频生成标准动作模板

        Args:
            exercise: 动作类型（当前仅支持 "squat"）
            video: 标准动作视频文件
            name: 模板名称
            view: 拍摄角度（side/front/diagonal）
            version: 版本号

        Returns:
            模板信息
        """
        # 验证拍摄角度
        valid_views = ["side", "front", "diagonal"]
        if view not in valid_views:
            raise HTTPException(status_code=400, detail=f"无效的拍摄角度: {view}，可选值: {valid_views}")

        # 临时保存上传的视频
        temp_dir = Path(settings.storage_root) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_path = temp_dir / f"template_video_{uuid4().hex[:8]}.mp4"

        try:
            # 保存上传的视频文件
            with open(temp_path, 'wb') as f:
                f.write(video.file.read())

            # 生成模板
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
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)