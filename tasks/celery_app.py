from celery import Celery

from config import get_settings

settings = get_settings()

celery_app = Celery(
    "nexus",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.timezone = settings.tz
celery_app.conf.task_default_queue = "nexus"
celery_app.conf.imports = ("tasks.scheduled_tasks",)
