from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "consight",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.backup",
        "app.workers.matching",
        "app.workers.whatsapp",
        "app.workers.ml_retrain",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "backup-to-sqlite-hourly": {
            "task": "app.workers.backup.backup_to_sqlite",
            "schedule": 3600.0,
        },
        "retrain-delay-model-daily": {
            "task": "app.workers.ml_retrain.retrain_delay_model",
            "schedule": 86400.0,  # Daily
        },
        "predict-all-projects-6hourly": {
            "task": "app.workers.ml_retrain.predict_all_projects",
            "schedule": 21600.0,  # Every 6 hours
        },
    },
)