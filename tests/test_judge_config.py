"""Tests for judge model and temperature configuration.

Covers:
- QualityScorer stores judge_temperature and passes it to the scoring function
- _resolve_scorers falls back judge_model to model_name when not specified
- _resolve_scorers passes judge_model and judge_temperature to QualityScorer
- EvalRequest accepts judge_model and judge_temperature with correct defaults
- CreateJudgeRequest validates name format
"""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError
from server.scoring import QualityScorer, score_response_sync
from server.evaluation import _resolve_scorers
from server.routes.evaluate import EvalRequest, CreateJudgeRequest


# --- QualityScorer ---

def test_quality_scorer_default_temperature():
    scorer = QualityScorer(judge_model="my-model")
    assert scorer.judge_temperature == 0.0


def test_quality_scorer_stores_custom_temperature():
    scorer = QualityScorer(judge_model="my-model", judge_temperature=0.7)
    assert scorer.judge_temperature == 0.7


def test_quality_scorer_passes_temperature_to_score_function():
    scorer = QualityScorer(judge_model="some-model", judge_temperature=0.5)
    with patch("server.scoring.score_response_sync", return_value=(4.0, "Good")) as mock_score:
        from mlflow.entities import Feedback
        result = scorer(
            inputs={"request": "What is 2+2?"},
            outputs={"response": "4"},
        )
        mock_score.assert_called_once_with("What is 2+2?", "4", "some-model", 0.5)
    assert isinstance(result, Feedback)


# --- score_response_sync temperature parameter ---

def test_score_response_sync_sends_temperature():
    with patch("server.scoring.get_workspace_host", return_value="https://example.databricks.com"), \
         patch("server.scoring.get_oauth_token", return_value="token123"), \
         patch("server.scoring.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "SCORE: 4.0\nRATIONALE: Good response"}}]
        }
        mock_post.return_value = mock_resp

        score, rationale = score_response_sync("prompt text", "response text", "my-model", temperature=0.3)

        payload = mock_post.call_args.kwargs["json"]
        assert payload["temperature"] == 0.3
        assert score == 4.0
        assert rationale == "Good response"


def test_score_response_sync_default_temperature_is_zero():
    with patch("server.scoring.get_workspace_host", return_value="https://example.databricks.com"), \
         patch("server.scoring.get_oauth_token", return_value="token123"), \
         patch("server.scoring.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "SCORE: 3.0\nRATIONALE: Average"}}]
        }
        mock_post.return_value = mock_resp

        score_response_sync("prompt", "response", "my-model")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["temperature"] == 0.0


# --- _resolve_scorers ---

def test_resolve_scorers_uses_model_name_when_judge_model_not_set():
    scorers = _resolve_scorers(scorer_name=None, model_name="prompt-model")
    assert len(scorers) == 1
    scorer = scorers[0]
    assert isinstance(scorer, QualityScorer)
    assert scorer.judge_model == "prompt-model"


def test_resolve_scorers_uses_explicit_judge_model():
    scorers = _resolve_scorers(scorer_name=None, model_name="prompt-model", judge_model="judge-model")
    assert len(scorers) == 1
    scorer = scorers[0]
    assert isinstance(scorer, QualityScorer)
    assert scorer.judge_model == "judge-model"


def test_resolve_scorers_passes_judge_temperature():
    scorers = _resolve_scorers(scorer_name=None, model_name="prompt-model", judge_temperature=0.4)
    assert len(scorers) == 1
    assert scorers[0].judge_temperature == 0.4


def test_resolve_scorers_builtin_ignores_judge_model_and_temperature():
    scorers = _resolve_scorers(
        scorer_name="safety",
        model_name="prompt-model",
        judge_model="ignored-model",
        judge_temperature=0.9,
    )
    # Built-in MLflow scorers manage their own model — QualityScorer should not be used
    assert len(scorers) == 1
    assert not isinstance(scorers[0], QualityScorer)


# --- EvalRequest defaults ---

def test_eval_request_judge_defaults():
    req = EvalRequest(
        prompt_name="main.prompts.my_prompt",
        prompt_version="1",
        model_name="databricks-llama",
        dataset_catalog="main",
        dataset_schema="eval_data",
        dataset_table="test_table",
        column_mapping={"topic": "topic_col"},
    )
    assert req.judge_model is None
    assert req.judge_temperature == 0.0


def test_eval_request_accepts_judge_model_and_temperature():
    req = EvalRequest(
        prompt_name="main.prompts.my_prompt",
        prompt_version="1",
        model_name="databricks-llama",
        dataset_catalog="main",
        dataset_schema="eval_data",
        dataset_table="test_table",
        column_mapping={"topic": "topic_col"},
        judge_model="databricks-claude-sonnet",
        judge_temperature=0.2,
    )
    assert req.judge_model == "databricks-claude-sonnet"
    assert req.judge_temperature == 0.2


# --- CreateJudgeRequest name validation ---

BASE_JUDGE_KWARGS = dict(type="custom", instructions="Score it.")


@pytest.mark.parametrize("name", [
    "tone_check",
    "relevance_scorer",
    "my_judge",
    "judge1",
    "a",
    "abc123",
])
def test_create_judge_request_valid_names(name):
    req = CreateJudgeRequest(name=name, **BASE_JUDGE_KWARGS)
    assert req.name == name


@pytest.mark.parametrize("name", [
    "Tone Check",          # spaces + uppercase
    "tone check",          # space
    "ToneCheck",           # uppercase
    "1judge",              # starts with digit
    "_judge",              # starts with underscore
    "tone-check",          # hyphen
    "tone.check",          # dot
    "",                    # empty
    "judge!",              # special char
])
def test_create_judge_request_invalid_names(name):
    with pytest.raises(ValidationError):
        CreateJudgeRequest(name=name, **BASE_JUDGE_KWARGS)
