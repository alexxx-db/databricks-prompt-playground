"""Tests for prompt creation and versioning API routes.

Covers:
- POST /api/prompts  — create a new prompt
- POST /api/prompts/versions  — save a new version of an existing prompt
"""

from unittest.mock import patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from server.routes.prompts import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /api/prompts — create a new prompt
# ---------------------------------------------------------------------------

def test_create_prompt_success(client):
    with patch("server.routes.prompts.create_prompt") as mock_create:
        mock_create.return_value = {
            "name": "main.prompts.my_prompt",
            "version": "1",
        }
        response = client.post("/api/prompts", json={
            "name": "main.prompts.my_prompt",
            "template": "Answer: {{question}}",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "main.prompts.my_prompt"
    assert data["version"] == "1"


def test_create_prompt_with_description(client):
    with patch("server.routes.prompts.create_prompt") as mock_create:
        mock_create.return_value = {
            "name": "main.prompts.my_prompt",
            "version": "1",
        }
        response = client.post("/api/prompts", json={
            "name": "main.prompts.my_prompt",
            "template": "Answer: {{question}}",
            "description": "A helpful Q&A prompt",
        })
        _, kwargs = mock_create.call_args
        assert kwargs.get("description") == "A helpful Q&A prompt"

    assert response.status_code == 200


def test_create_prompt_missing_name_returns_400(client):
    response = client.post("/api/prompts", json={
        "name": "",
        "template": "Answer: {{question}}",
    })
    assert response.status_code == 400
    assert "name" in response.json()["detail"].lower()


def test_create_prompt_whitespace_name_returns_400(client):
    response = client.post("/api/prompts", json={
        "name": "   ",
        "template": "Answer: {{question}}",
    })
    assert response.status_code == 400


def test_create_prompt_empty_template_returns_400(client):
    response = client.post("/api/prompts", json={
        "name": "main.prompts.my_prompt",
        "template": "",
    })
    assert response.status_code == 400
    assert "template" in response.json()["detail"].lower()


def test_create_prompt_already_exists_returns_409(client):
    with patch("server.routes.prompts.create_prompt") as mock_create:
        mock_create.side_effect = Exception("ALREADY_EXISTS: prompt exists")
        response = client.post("/api/prompts", json={
            "name": "main.prompts.existing",
            "template": "Hello {{name}}",
        })

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_create_prompt_other_error_returns_500(client):
    with patch("server.routes.prompts.create_prompt") as mock_create:
        mock_create.side_effect = Exception("Unexpected MLflow error")
        response = client.post("/api/prompts", json={
            "name": "main.prompts.my_prompt",
            "template": "Hello {{name}}",
        })

    assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/prompts/versions — save a new version of an existing prompt
# ---------------------------------------------------------------------------

def test_save_version_success(client):
    with patch("server.routes.prompts.create_prompt_version") as mock_ver:
        mock_ver.return_value = {
            "name": "main.prompts.my_prompt",
            "version": "2",
        }
        response = client.post("/api/prompts/versions", json={
            "name": "main.prompts.my_prompt",
            "template": "Updated answer: {{question}}",
        })

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2"


def test_save_version_missing_name_returns_400(client):
    response = client.post("/api/prompts/versions", json={
        "name": "",
        "template": "Some template",
    })
    assert response.status_code == 400


def test_save_version_empty_template_returns_400(client):
    response = client.post("/api/prompts/versions", json={
        "name": "main.prompts.my_prompt",
        "template": "",
    })
    assert response.status_code == 400


def test_save_version_prompt_not_found_returns_404(client):
    with patch("server.routes.prompts.create_prompt_version") as mock_ver:
        mock_ver.side_effect = Exception("NOT_FOUND: prompt not found")
        response = client.post("/api/prompts/versions", json={
            "name": "main.prompts.nonexistent",
            "template": "Hello {{name}}",
        })

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_save_version_other_error_returns_500(client):
    with patch("server.routes.prompts.create_prompt_version") as mock_ver:
        mock_ver.side_effect = Exception("Internal MLflow error")
        response = client.post("/api/prompts/versions", json={
            "name": "main.prompts.my_prompt",
            "template": "Hello {{name}}",
        })

    assert response.status_code == 500
