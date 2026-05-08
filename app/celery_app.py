from celery import Celery
from app.core.config import settings
celery_app = Celery(
    "ml_service",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL, 
)

celery_app.conf.task_routes = {
    "worker.tasks.*": {"queue": "ml_queue"}
}
celery_app.autodiscover_tasks(["worker"])