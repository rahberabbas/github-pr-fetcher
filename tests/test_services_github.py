import pytest
from fastapi import HTTPException
from app.services.github import fetch_pr_details

@pytest.fixture
def mock_requests(mocker):
    return mocker.patch("requests.get")

def test_fetch_pr_details_success(mock_requests):
    mock_requests.return_value.status_code = 200
    mock_requests.return_value.json.return_value = {"diff_url": "mock_diff_url"}

    result = fetch_pr_details("https://github.com/user/repo.git", 1)
    assert result == "mock_diff_url"

def test_fetch_pr_details_404(mock_requests):
    mock_requests.return_value.status_code = 404

    with pytest.raises(HTTPException) as exc_info:
        fetch_pr_details("https://github.com/user/repo.git", 1)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Pull Request not found."

def test_fetch_pr_details_invalid_url():
    with pytest.raises(ValueError):
        fetch_pr_details("invalid_url", 1)
