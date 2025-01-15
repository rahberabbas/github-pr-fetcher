web: uvicorn app:app --host=0.0.0.0 --port=8000
worker: celery -A app.celery.worker.celery worker --loglevel=info --pool=threads