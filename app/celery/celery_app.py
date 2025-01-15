from celery import Celery
from app.core.config import config_provider

# Celery application configuration
celery = Celery(
    "tasks",
    broker=config_provider.get_redis_url(),  # Redis as the message broker
    backend=config_provider.get_redis_url(),  # Redis as the result backend
    include=["app.celery.tasks.automated_code_review"]
)

