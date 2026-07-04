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
            user_id=current_user.id if current_user else None,
        )

    @router.get("/tasks")
    def list_analysis_tasks(
        limit: int = 50,
        offset: int = 0,
        current_user=Depends(get_current_active_user) if get_current_active_user else None,
    ):
        uid = None if (current_user and current_user.role == "admin") else (current_user.id if current_user else None)
        tasks = task_service.list_tasks(limit=limit, offset=offset, user_id=uid)
        total = task_service.count_tasks() if hasattr(task_service, "count_tasks") else len(tasks)
        return {"items": tasks, "total": total}

    @router.delete("/tasks/{task_id}")
    def delete_analysis_task(
        task_id: str,
        current_user=Depends(get_current_active_user),
    ):
        uid = None if current_user.role == "admin" else current_user.id
        deleted = task_service.delete_task(task_id, user_id=uid)
        if not deleted:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted", "task_id": task_id}
