"""Config route — exposes catalog/schema env vars to the frontend."""

import os
from fastapi import APIRouter

router = APIRouter(prefix="/api/config")


@router.get("")
async def get_config():
    """Return catalog/schema configuration read from environment variables."""
    prompt_catalog = os.environ.get("PROMPT_CATALOG", "main")
    prompt_schema = os.environ.get("PROMPT_SCHEMA", "prompts")
    eval_schema = os.environ.get("EVAL_SCHEMA", "eval_data")
    experiment_name = os.environ.get(
        "MLFLOW_EXPERIMENT_NAME", "/Shared/prompt-playground-evaluation"
    )
    return {
        "prompt_catalog": prompt_catalog,
        "prompt_schema": prompt_schema,
        "eval_catalog": prompt_catalog,
        "eval_schema": eval_schema,
        "mlflow_experiment_name": experiment_name,
    }
