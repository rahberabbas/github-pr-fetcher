from fastapi import HTTPException
import requests
from typing import Optional

# Utility function to fetch PR details
def fetch_pr_details(repo_url: str, pr_number: int, github_token: Optional[str] = None) -> str:
    """
    Fetch details of a pull request from a GitHub repository.

    Args:
        repo_url (str): The URL of the GitHub repository.
        pr_number (int): The number of the pull request.
        github_token (Optional[str]): Personal access token for GitHub API (optional).

    Returns:
        str: The diff_url of the pull request.

    Raises:
        ValueError: If the repository URL format is invalid.
        HTTPException: If the pull request is not found or any other error occurs.
    """
    # Extract repository owner and name from the URL
    try:
        repo_parts = repo_url.rstrip("/").split("/")
        owner = repo_parts[-2]
        repo = repo_parts[-1].removesuffix(".git")
    except Exception:
        raise ValueError("Invalid repository URL format.")

    # Construct the GitHub API URL
    pr_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    # Set up headers for the API request
    headers = {}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"

    # Make the request to GitHub API
    response = requests.get(pr_api_url, headers=headers)

    if response.status_code == 200:
        return response.json().get("diff_url")
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="Pull Request not found.")
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Error fetching PR details: {response.json().get('message', 'Unknown error')}"
        )