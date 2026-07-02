from app.api.deps import get_current_active_user
from app.schemas.analysis import AnalysisTaskCreate
from app.services.task.task_service import task_service

try:
    from fastapi import APIRouter, Depends
except ModuleNotFoundError:
    APIRouter = Depends = None

router = APIRouter(prefix="/analysis", tags=["analysis"]) if APIRouter else None


if router:
    @router.post("/tasks", status_code=201)
    def create_analysis_task(
        payload: AnalysisTaskCreate,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        return task_service.create_task(
            exercise=payload.exercise,
            source_uri=payload.source_uri,
        )

    @router.get("/tasks/{task_id}")
    def get_analysis_task(
        task_id: str,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        task = task_service.get_task(task_id)
        if task is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Task not found")
        return task
