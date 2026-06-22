from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class AnalysisTask:
    task_id: str
    exercise: str
    source_uri: str
    status: str
    created_at: str
    output_uri: str | None = None
    error_message: str | None = None

    def to_dict(self):
        return asdict(self)


class TaskService:
    def __init__(self):
        self._tasks: dict[str, AnalysisTask] = {}

    def create_task(
        self,
        exercise: str,
        source_uri: str,
        status: str = "pending",
        output_uri: str | None = None,
    ) -> AnalysisTask:
        task = AnalysisTask(
            task_id=str(uuid4()),
            exercise=exercise,
            source_uri=source_uri,
            status=status,
            created_at=datetime.now(timezone.utc).isoformat(),
            output_uri=output_uri,
        )
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> AnalysisTask:
        return self._tasks.get(
            task_id,
            AnalysisTask(
                task_id=task_id,
                exercise="unknown",
                source_uri="",
                status="failed",
                created_at=datetime.now(timezone.utc).isoformat(),
                error_message="task not found",
            ),
        )


task_service = TaskService()
