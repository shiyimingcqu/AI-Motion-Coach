from app.app_placeholder import not_configured_message
from app.workers.celery_app import celery_app


if celery_app:
    @celery_app.task(name="analyze_video")
    def analyze_video(task_id: str):
        return {"task_id": task_id, "status": "reserved"}
else:
    def analyze_video(task_id: str):
        return {"task_id": task_id, "status": "skipped", "reason": not_configured_message()}
