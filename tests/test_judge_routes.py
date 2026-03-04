"""Tests for judge management routes in /api/eval.

Covers:
- GET /api/eval/judges         — list registered scorers
- GET /api/eval/judges/detail  — get scorer instructions/guidelines
- POST /api/eval/judges        — create/update custom or guidelines judge
- DELETE /api/eval/judges      — delete a registered scorer
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.routes.evaluate import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _base_mlflow_patches():
    """Common patches needed for judge routes that call mlflow directly."""
    return [
        patch("server.routes.evaluate.configure_mlflow"),
        patch("server.routes.evaluate.mlflow.set_experiment"),
        patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None),
    ]


# ---------------------------------------------------------------------------
# GET /api/eval/judges
# ---------------------------------------------------------------------------

class TestListJudges:

    def test_returns_judge_names(self, client):
        scorer1 = MagicMock()
        scorer1.name = "tone_check"
        scorer2 = MagicMock()
        scorer2.name = "relevance"

        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.scorers.list_scorers", return_value=[scorer1, scorer2]):
            resp = client.get("/api/eval/judges")

        assert resp.status_code == 200
        judges = resp.json()["judges"]
        assert len(judges) == 2
        names = [j["name"] for j in judges]
        assert "tone_check" in names
        assert "relevance" in names

    def test_empty_list_when_no_scorers(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.scorers.list_scorers", return_value=[]):
            resp = client.get("/api/eval/judges")

        assert resp.status_code == 200
        assert resp.json()["judges"] == []

    def test_error_returns_500(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.scorers.list_scorers", side_effect=RuntimeError("MLflow down")):
            resp = client.get("/api/eval/judges")

        assert resp.status_code == 500
        assert "MLflow down" in resp.json()["detail"]

    def test_accepts_experiment_name_param(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment") as mock_set_exp, \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.scorers.list_scorers", return_value=[]):
            resp = client.get("/api/eval/judges?experiment_name=my_exp")

        assert resp.status_code == 200
        mock_set_exp.assert_called_once_with("my_exp")


# ---------------------------------------------------------------------------
# GET /api/eval/judges/detail
# ---------------------------------------------------------------------------

class TestGetJudgeDetail:

    def test_custom_judge_returns_instructions(self, client):
        scorer = MagicMock()
        scorer.model_dump.return_value = {"instructions": "Score on clarity.", "guidelines": None}
        scorer.guidelines = None  # prevent auto-created MagicMock truthy attribute

        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.get_scorer", return_value=scorer):
            resp = client.get("/api/eval/judges/detail?name=my_judge")

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "my_judge"
        assert data["type"] == "custom"
        assert data["instructions"] == "Score on clarity."
        assert data["guidelines"] is None

    def test_guidelines_judge_returns_guidelines(self, client):
        scorer = MagicMock()
        scorer.model_dump.return_value = {
            "guidelines": ["Be concise", "Be accurate"],
            "instructions": None,
        }

        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.get_scorer", return_value=scorer):
            resp = client.get("/api/eval/judges/detail?name=my_guidelines_judge")

        data = resp.json()
        assert data["type"] == "guidelines"
        assert data["guidelines"] == ["Be concise", "Be accurate"]
        assert data["instructions"] is None

    def test_falls_back_to_attributes_when_model_dump_empty(self, client):
        """Databricks-created scorers may only expose data via attributes, not model_dump."""
        scorer = MagicMock(spec=["model_dump", "instructions", "guidelines"])
        scorer.model_dump.return_value = {}  # empty model_dump
        scorer.instructions = "Score quality."
        scorer.guidelines = None

        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.get_scorer", return_value=scorer):
            resp = client.get("/api/eval/judges/detail?name=db_judge")

        data = resp.json()
        assert data["type"] == "custom"
        assert data["instructions"] == "Score quality."

    def test_requires_name_param(self, client):
        resp = client.get("/api/eval/judges/detail")
        assert resp.status_code == 422

    def test_error_returns_500(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.get_scorer", side_effect=RuntimeError("Not found")):
            resp = client.get("/api/eval/judges/detail?name=missing_judge")

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /api/eval/judges
# ---------------------------------------------------------------------------

class TestCreateJudge:

    def _post_judge(self, client, payload):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None):
            return client.post("/api/eval/judges", json=payload)

    def test_create_custom_judge_success(self, client):
        mock_judge = MagicMock()
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.judges.make_judge", return_value=mock_judge):
            resp = client.post("/api/eval/judges", json={
                "name": "tone_check",
                "type": "custom",
                "instructions": "Rate the tone of the response.",
            })

        assert resp.status_code == 200
        assert resp.json()["name"] == "tone_check"
        assert resp.json()["status"] == "registered"
        mock_judge.register.assert_called_once()

    def test_create_guidelines_judge_success(self, client):
        mock_judge = MagicMock()
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.scorers.Guidelines", return_value=mock_judge):
            resp = client.post("/api/eval/judges", json={
                "name": "quality_check",
                "type": "guidelines",
                "guidelines": ["Be concise", "Be accurate"],
            })

        assert resp.status_code == 200
        assert resp.json()["name"] == "quality_check"
        mock_judge.register.assert_called_once()

    def test_custom_judge_missing_instructions_returns_400(self, client):
        resp = self._post_judge(client, {
            "name": "my_judge",
            "type": "custom",
            # instructions omitted
        })
        assert resp.status_code == 400
        assert "instructions" in resp.json()["detail"]

    def test_guidelines_judge_missing_guidelines_returns_400(self, client):
        resp = self._post_judge(client, {
            "name": "my_judge",
            "type": "guidelines",
            # guidelines omitted
        })
        assert resp.status_code == 400
        assert "guidelines" in resp.json()["detail"]

    def test_invalid_type_returns_400(self, client):
        resp = self._post_judge(client, {
            "name": "my_judge",
            "type": "unsupported_type",
            "instructions": "something",
        })
        assert resp.status_code == 400
        assert "unsupported_type" in resp.json()["detail"]

    def test_empty_name_returns_422(self, client):
        resp = self._post_judge(client, {
            "name": "",
            "type": "custom",
            "instructions": "Rate it.",
        })
        assert resp.status_code == 422

    def test_update_flag_deletes_then_recreates(self, client):
        mock_judge = MagicMock()
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.judges.make_judge", return_value=mock_judge), \
             patch("mlflow.genai.scorers.delete_scorer") as mock_delete:
            resp = client.post("/api/eval/judges", json={
                "name": "existing_judge",
                "type": "custom",
                "instructions": "Updated instructions.",
                "is_update": True,
            })

        assert resp.status_code == 200
        assert resp.json()["status"] == "updated"
        mock_delete.assert_called_once_with(name="existing_judge")

    def test_update_false_does_not_delete(self, client):
        mock_judge = MagicMock()
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.judges.make_judge", return_value=mock_judge), \
             patch("mlflow.genai.scorers.delete_scorer") as mock_delete:
            resp = client.post("/api/eval/judges", json={
                "name": "new_judge",
                "type": "custom",
                "instructions": "New judge.",
                "is_update": False,
            })

        assert resp.status_code == 200
        assert resp.json()["status"] == "registered"
        mock_delete.assert_not_called()

    def test_workspace_error_returns_500(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("server.routes.evaluate.mlflow.set_experiment"), \
             patch("server.routes.evaluate.mlflow.get_experiment_by_name", return_value=None), \
             patch("mlflow.genai.judges.make_judge", side_effect=RuntimeError("Permission denied")):
            resp = client.post("/api/eval/judges", json={
                "name": "my_judge",
                "type": "custom",
                "instructions": "Rate it.",
            })

        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/eval/judges
# ---------------------------------------------------------------------------

class TestDeleteJudge:

    def test_delete_success(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.delete_scorer") as mock_delete:
            resp = client.delete("/api/eval/judges?name=tone_check")

        assert resp.status_code == 200
        assert resp.json()["name"] == "tone_check"
        assert resp.json()["status"] == "deleted"
        mock_delete.assert_called_once_with(name="tone_check")

    def test_delete_requires_name_param(self, client):
        resp = client.delete("/api/eval/judges")
        assert resp.status_code == 422

    def test_delete_error_returns_500(self, client):
        with patch("server.routes.evaluate.configure_mlflow"), \
             patch("mlflow.genai.scorers.delete_scorer", side_effect=RuntimeError("Not found")):
            resp = client.delete("/api/eval/judges?name=nonexistent")

        assert resp.status_code == 500
