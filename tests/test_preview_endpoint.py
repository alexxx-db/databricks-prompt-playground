"""Tests for POST /api/preview — renders a prompt without calling a model.

Covers:
- Returns rendered_prompt with variables substituted
- Returns system_prompt when the template has one
- Returns system_prompt=None when no system section
- Returns original template and variable list
- Returns 404 when prompt version not found
- Returns 500 on unexpected error
"""

import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.routes.run import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


_PLAIN_TEMPLATE = {
    "template": "Tell me about {{topic}}.",
    "variables": ["topic"],
    "system_prompt": None,
}

_SYSTEM_TEMPLATE = {
    "template": "Help with {{topic}}.",
    "variables": ["company", "topic"],
    "system_prompt": "You are an assistant for {{company}}.",
}


def _preview(client, name, version, variables=None):
    payload = {
        "prompt_name": name,
        "prompt_version": version,
    }
    if variables is not None:
        payload["variables"] = variables
    return client.post("/api/preview", json=payload)


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------

def test_preview_renders_user_template(client):
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1", variables={"topic": "Python"})

    assert resp.status_code == 200
    assert resp.json()["rendered_prompt"] == "Tell me about Python."


def test_preview_substitutes_all_variables(client):
    with patch("server.routes.run.get_prompt_template", return_value=_SYSTEM_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1",
                        variables={"company": "Acme", "topic": "billing"})

    assert resp.status_code == 200
    assert resp.json()["rendered_prompt"] == "Help with billing."


def test_preview_leaves_unset_variable_as_placeholder(client):
    """Variables not provided are left as {{placeholder}} in the output."""
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1", variables={})

    assert "{{topic}}" in resp.json()["rendered_prompt"]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def test_preview_returns_system_prompt_when_present(client):
    with patch("server.routes.run.get_prompt_template", return_value=_SYSTEM_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1",
                        variables={"company": "Acme", "topic": "billing"})

    assert resp.json()["system_prompt"] == "You are an assistant for Acme."


def test_preview_system_prompt_none_when_absent(client):
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1", variables={"topic": "test"})

    assert resp.json()["system_prompt"] is None


def test_preview_system_prompt_variables_substituted(client):
    with patch("server.routes.run.get_prompt_template", return_value=_SYSTEM_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1",
                        variables={"company": "Databricks", "topic": "SQL"})

    assert resp.json()["system_prompt"] == "You are an assistant for Databricks."


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

def test_preview_returns_template_field(client):
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1")

    assert resp.json()["template"] == "Tell me about {{topic}}."


def test_preview_returns_variables_list(client):
    with patch("server.routes.run.get_prompt_template", return_value=_SYSTEM_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1")

    assert "company" in resp.json()["variables"]
    assert "topic" in resp.json()["variables"]


def test_preview_response_has_expected_keys(client):
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE):
        resp = _preview(client, "main.prompts.test", "1")

    keys = set(resp.json().keys())
    assert {"rendered_prompt", "system_prompt", "template", "variables"}.issubset(keys)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_preview_not_found_returns_404(client):
    with patch("server.routes.run.get_prompt_template",
               side_effect=ValueError("Prompt version not found")):
        resp = _preview(client, "main.prompts.gone", "99")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_preview_unexpected_error_returns_500(client):
    with patch("server.routes.run.get_prompt_template",
               side_effect=Exception("MLflow connection failed")):
        resp = _preview(client, "main.prompts.test", "1")

    assert resp.status_code == 500


def test_preview_missing_required_fields_returns_422(client):
    resp = client.post("/api/preview", json={})
    assert resp.status_code == 422


def test_preview_no_model_call_made(client):
    """Preview must never call call_model — it's a dry-run endpoint."""
    with patch("server.routes.run.get_prompt_template", return_value=_PLAIN_TEMPLATE), \
         patch("server.routes.run.call_model") as mock_call:
        _preview(client, "main.prompts.test", "1")

    mock_call.assert_not_called()
