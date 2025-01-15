import pytest
from app.services.ai_agenct import GitHubPRReviewAgent

@pytest.fixture
def mock_ai_agent(mocker):
    mock_reviewer = mocker.patch("app.services.ai_agent.GitHubPRReviewAgent")
    mock_reviewer.return_value.review_pr.return_value = {
        "summary": {"total_files": 1, "total_issues": 3},
        "files": [{"name": "file1.py", "issues": []}]
    }
    return mock_reviewer
