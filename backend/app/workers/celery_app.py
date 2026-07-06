from app.core.config import settings

try:
    from celery import Celery
except ModuleNotFoundError:
    Celery = None


celery_app = (
    Celery("pose_worker", broker=settings.redis_url, backend=settings.redis_url)
    if Celery
    else None
)
