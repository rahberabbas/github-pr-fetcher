from celery import Celery
from app.celery.celery_app import celery

if __name__ == "__main__":
    # Start the Celery worker
    celery.start()
