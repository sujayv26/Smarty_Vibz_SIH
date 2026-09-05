from app.core.config import settings
from app.core.celery_app import celery_app

__all__ = ["settings", "celery_app"]