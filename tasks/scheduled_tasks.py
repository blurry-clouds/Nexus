from loguru import logger

from tasks.celery_app import celery_app


@celery_app.task(name="tasks.healthcheck")
def healthcheck_task() -> str:
    logger.info("celery.healthcheck")
    return "ok"
