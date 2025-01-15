from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_app_initialization():
    response = client.get("/")
    assert response.status_code == 404  # Root route not defined
    assert app.title == "GitHub PR Fetcher"
    assert app.version == "1.0.0"
