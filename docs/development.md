# Development

## Local Dev Server

```bash
cd src && \
PROMPT_CATALOG=your_catalog PROMPT_SCHEMA=prompts EVAL_SCHEMA=eval_data \
MLFLOW_EXPERIMENT_NAME=/Shared/prompt-playground-evaluation \
SQL_WAREHOUSE_ID=<your-warehouse-id> \
uv run --no-project --python 3.11 \
  --with "fastapi>=0.115.0,uvicorn[standard]>=0.30.0,aiohttp>=3.9.0,databricks-sdk>=0.30.0,pydantic>=2.0.0,mlflow[databricks]>=3.1.0,python-multipart>=0.0.9,requests" \
  uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Authenticate first with `databricks auth login --host https://<your-workspace>.azuredatabricks.net`.
Find your warehouse ID in **SQL > Warehouses > \<name\> > Connection details**.

## Rebuild Frontend

```bash
cd src/frontend && npm run build
```

`dist/` is pre-built and committed. Rebuild only needed after frontend changes.

## Running Tests

```bash
uv run --no-project --python 3.11 \
  --with "fastapi>=0.115.0,httpx>=0.27.0,pytest,mlflow[databricks]>=3.1.0,databricks-sdk>=0.30.0,pydantic>=2.0.0,aiohttp>=3.9.0,uvicorn,requests" \
  pytest tests/ -v --ignore=tests/test_template_rendering.py
```

- `tests/test_template_rendering.py` — requires a live Databricks connection, excluded from local runs

---

## Gotchas

1. **`MANAGE` privilege**: Must be granted explicitly — `ALL PRIVILEGES` does NOT include it. Routes return 403 with actionable GRANT instructions.
2. **Temperature errors**: Some models reject temperature ≠ 1.0. `llm.py` detects and surfaces a user-friendly error.
3. **MLflow `search_traces`**: Must use `return_type="list"` — default returns DataFrame; iterating gives column names, not rows.
4. **Experiments filtered by catalog/schema**: `search_runs` batched in chunks of 100 (MLflow API limit).
5. **`dist/` tracking**: Use `git add -f` if `.gitignore` blocks the built assets.
6. **Branch switching**: Always `git stash` before switching. `dist/` conflicts are safe to resolve with `--theirs` or `--ours` — rebuild after.
