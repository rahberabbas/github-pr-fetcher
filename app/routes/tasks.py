from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult
from app.models.request_models import FetchPRPayload
from app.celery.tasks.automated_code_review import fetch_github_pr
from app.celery.celery_app import celery
import logging

# Initialize logger
from app.core.logging_config import logger

router = APIRouter()

@router.post("/analyze-pr", summary="Fetch GitHub PR details and Review it in background")
def create_task(payload: FetchPRPayload):
    logger.info(f"Received PR analyze request: {payload.github_repo_url} - PR#{payload.pr_number}")
    github_repo_url = str(payload.github_repo_url)
    try:
        task = fetch_github_pr.delay(github_repo_url, payload.pr_number, payload.access_token)
        logger.info(f"Task {task.id} started for PR#{payload.pr_number}")
        return {"task_id": task.id}
    except Exception as e:
        logger.error(f"Error starting task for PR#{payload.pr_number}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting task")

@router.get("/status/{task_id}", summary="Get task status")
def get_task_status(task_id: str):
    logger.info(f"Fetching status for task {task_id}")
    task = AsyncResult(task_id, app=celery)
    
    state_messages = {
        "PENDING": {"status": "pending", "message": "Task is waiting to be processed"},
        "PROCESSING": {"status": "processing", "message": "Task is processed"},
        "SUCCESS": {"status": "success"},
        "FAILURE": {"status": "failure", "message": str(task.result)},
    }

    # Get the state details or fall back to a default state
    response = state_messages.get(
        task.state,
        {"status": task.state}  # Default case if state is unrecognized
    )
    
    # Add the task_id to the response
    response["task_id"] = task_id
    logger.info(f"Task {task_id} status: {response['status']}")
    return response

@router.get("/results/{task_id}", summary="Get task result")
def get_task_result(task_id: str):
    logger.info(f"Fetching result for task {task_id}")
    task = AsyncResult(task_id, app=celery)

    if not task.ready():
        logger.warning(f"Task {task_id} result not ready yet")
        raise HTTPException(status_code=404, detail="Task result not ready yet")

    logger.info(f"Task {task_id} completed with result: {task.result}")
    return {"task_id": task_id, "status": "completed", "result": task.result}

