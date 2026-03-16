"""Shared MLflow configuration and experiment helpers.

Centralises the MLflow tracking/registry setup that was previously duplicated
across mlflow_client.py, routes/run.py, and routes/evaluate.py.
"""

import os
import logging
import mlflow
from mlflow import MlflowClient
from server.config import get_workspace_host, IS_DATABRICKS_APP

logger = logging.getLogger(__name__)

EXPERIMENT_NAME = os.environ.get(
    "MLFLOW_EXPERIMENT_NAME",
    "/Shared/prompt-playground-evaluation",
)


def configure_mlflow():
    """Set up MLflow tracking and registry URIs for Databricks."""
    if IS_DATABRICKS_APP:
        mlflow.set_tracking_uri("databricks")
        mlflow.set_registry_uri("databricks-uc")
    else:
        profile = os.environ.get("DATABRICKS_PROFILE")
        mlflow.set_tracking_uri(f"databricks://{profile}" if profile else "databricks")
        mlflow.set_registry_uri("databricks-uc")


def get_mlflow_client() -> MlflowClient:
    """Return a configured MlflowClient instance."""
    configure_mlflow()
    return MlflowClient()


def get_experiment_id(experiment_name: str | None = None) -> str | None:
    """Look up experiment ID by name, falling back to the default experiment."""
    try:
        configure_mlflow()
        name = experiment_name or EXPERIMENT_NAME
        exp = mlflow.get_experiment_by_name(name)
        return exp.experiment_id if exp else None
    except Exception as e:
        logger.warning("Could not get experiment: %s", e)
        return None


def experiment_url(experiment_id: str) -> str:
    """Build a workspace URL for an MLflow experiment."""
    return f"{get_workspace_host().rstrip('/')}/ml/experiments/{experiment_id}?searchFilter="
