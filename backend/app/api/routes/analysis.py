from app.schemas.analysis import AnalysisTaskCreate
from app.services.task.task_service import task_service

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None

router = APIRouter(prefix="/analysis", tags=["analysis"]) if APIRouter else None


if router:
    @router.post("/tasks", status_code=201)
    def create_analysis_task(payload: AnalysisTaskCreate):
        task = task_service.create_task(
            exercise=payload.exercise,
            source_uri=payload.source_uri,
        )
        return task.to_dict()

    @router.get("/tasks/{task_id}")
    def get_analysis_task(task_id: str):
        task = task_service.get_task(task_id)
        return task.to_dict()
