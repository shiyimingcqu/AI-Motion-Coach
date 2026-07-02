"""Task service — persisted to SQLite via SQLAlchemy ORM."""

from datetime import datetime, timezone
from uuid import uuid4

from app.db.session import SessionLocal
from app.models.entities import AnalysisTaskORM


class TaskService:
    """Analysis task CRUD, backed by the analysis_tasks table."""

    def create_task(
        self,
        exercise: str,
        source_uri: str,
        status: str = "pending",
        output_uri: str | None = None,
    ) -> dict:
        """Create a new analysis task and persist it."""
        if SessionLocal is None:
            raise RuntimeError("Database not available")

        db = SessionLocal()
        try:
            task = AnalysisTaskORM(
                task_id=str(uuid4()),
                exercise=exercise,
                source_uri=source_uri,
                status=status,
                output_uri=output_uri,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(task)
            db.commit()
            db.refresh(task)
            return task.to_dict()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get_task(self, task_id: str) -> dict | None:
        """Retrieve a task by its task_id."""
        if SessionLocal is None:
            return None

        db = SessionLocal()
        try:
            task = db.query(AnalysisTaskORM).filter(
                AnalysisTaskORM.task_id == task_id
            ).first()
            return task.to_dict() if task else None
        finally:
            db.close()

    def update_task(
        self,
        task_id: str,
        status: str | None = None,
        output_uri: str | None = None,
        error_message: str | None = None,
    ) -> dict | None:
        """Update task status / output / error."""
        if SessionLocal is None:
            return None

        db = SessionLocal()
        try:
            task = db.query(AnalysisTaskORM).filter(
                AnalysisTaskORM.task_id == task_id
            ).first()
            if not task:
                return None

            if status is not None:
                task.status = status
            if output_uri is not None:
                task.output_uri = output_uri
            if error_message is not None:
                task.error_message = error_message
            task.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(task)
            return task.to_dict()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def list_tasks(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        """List tasks, newest first."""
        if SessionLocal is None:
            return []

        db = SessionLocal()
        try:
            tasks = (
                db.query(AnalysisTaskORM)
                .order_by(AnalysisTaskORM.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [t.to_dict() for t in tasks]
        finally:
            db.close()


task_service = TaskService()
