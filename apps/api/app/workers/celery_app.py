from celery import Celery

from app.config import settings

celery_app = Celery("breero", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    timezone="UTC",
    beat_schedule={
        "publish-outbox": {"task": "app.workers.tasks.publish_outbox", "schedule": 10.0},
        "expire-bookings": {"task": "app.workers.tasks.expire_bookings", "schedule": 60.0},
    },
)
celery_app.autodiscover_tasks(["app.workers"])
