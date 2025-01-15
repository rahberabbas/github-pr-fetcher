from app.celery.celery_app import celery
from app.services.github import fetch_pr_details
from app.services.ai_agenct import reviewer
import logging
from app.core.logging_config import logger

@celery.task
def fetch_github_pr(github_repo_url: str, pr_number: int, access_token: str = None):
    logger.info(f"Started fetching PR details for {github_repo_url} - PR#{pr_number}")
    try:
        # Fetch PR details from GitHub
        detail = fetch_pr_details(github_repo_url, pr_number, access_token)
        logger.info(f"Successfully fetched PR details for {github_repo_url} - PR#{pr_number}")
        
        # Review PR using AI agent
        result = reviewer.review_pr(detail)
        logger.info(f"Completed review for PR#{pr_number}")
        return result
    except Exception as e:
        logger.error(f"Error fetching or reviewing PR#{pr_number}: {str(e)}")
        raise e