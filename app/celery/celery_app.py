from celery import Celery

# Celery application configuration
celery = Celery(
    "tasks",
    broker="redis://redis:6379/0",  # Redis as the message broker
    backend="redis://redis:6379/0",  # Redis as the result backend
    include=["app.celery.tasks.automated_code_review"]
)

