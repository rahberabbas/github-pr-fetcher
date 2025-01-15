import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_payload():
    return {
        "github_repo_url": "https://github.com/user/repo.git",
        "pr_number": 1,
        "access_token": "mock_access_token"
    }

def test_create_task(mock_payload):
    response = client.post("/analyze-pr", json=mock_payload)
    assert response.status_code == 200
    assert "task_id" in response.json()

def test_get_task_status_pending():
    task_id = "mock_task_id"
    response = client.get(f"/status/{task_id}")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "processing", "success", "failure"]

def test_get_task_result_not_ready():
    task_id = "mock_task_id"
    response = client.get(f"/results/{task_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task result not ready yet"
