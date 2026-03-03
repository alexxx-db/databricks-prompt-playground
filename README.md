# Prompt Playground

Prompt Playground is an interactive, no-code Databricks App for designing, testing, and evaluating prompts stored in the [Prompt Registry](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/). It enables product owners, prompt engineers, and both technical and non-technical users to iterate on prompt templates, run them against live model serving endpoints, and evaluate quality at scale — without writing code.

## What you can do

- **Manage prompts** — browse, create, and version prompt templates directly from the UI; no code required
- **Iterate interactively** — fill in `{{template_variables}}`, run against any model serving endpoint, and preview the fully rendered prompt before executing
- **Evaluate at scale** — run a prompt version against any Unity Catalog Delta table, auto-map dataset columns to template variables, score with built-in LLM-as-judge presets or your own custom judges, and triage low-scoring results in-app
- **Tightly integrated with Databricks** — every run and evaluation is logged as an MLflow trace with direct links to the Experiments UI, including prompt versions, model calls, scores, and judge reasoning; all data stays in your Unity Catalog environment

---

## Requirements

Before deploying, make sure you have:

- [ ] [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install.html) `>= 0.220.0` installed
- [ ] A **Unity Catalog catalog** with your MLflow Prompt Registry prompts (and optionally evaluation datasets)
- [ ] A **SQL Warehouse** running in your workspace (needed for eval dataset queries)
- [ ] A **model serving endpoint** — [Foundation Model API](https://docs.databricks.com/machine-learning/foundation-models/index.html) endpoints work out of the box
- [ ] **Workspace admin or** CAN_MANAGE permission on the catalog

---

## Installation

### 1. Authenticate with your workspace

```bash
databricks auth login --host https://<your-workspace>.azuredatabricks.net
```

Verify authentication:

```bash
databricks auth profiles
```

### 2. Extract and open the project

Unzip the file you received, then navigate into the folder:

```bash
unzip prompt-playground.zip
cd prompt-playground
```

### 3. Configure your SQL Warehouse

Open `databricks.yml` and set your warehouse. You have two options:

**Option A — resolve by name (recommended):**

Comment out the `warehouse_id` variable block and replace it with:

```yaml
variables:
  warehouse_id:
    description: "SQL Warehouse for eval queries"
    lookup:
      warehouse: "Serverless Starter Warehouse"   # replace with your warehouse name
```

**Option B — set the ID directly:**

```yaml
variables:
  warehouse_id:
    default: "abc1234def567890"   # find this in SQL > Warehouses > <name> > Connection details
```

### 4. Configure your catalog and schema

Open `src/app.yaml` and update the three env vars:

```yaml
env:
  - name: PROMPT_CATALOG
    value: "your_catalog"       # UC catalog where your prompts live
  - name: PROMPT_SCHEMA
    value: "prompts"            # Schema containing the MLflow Prompt Registry
  - name: EVAL_SCHEMA
    value: "eval_data"          # Schema containing evaluation dataset tables
```

### 5. (Optional) Configure serving endpoint access

The app's **model dropdown** is populated dynamically — it lists every chat-compatible serving endpoint the app's service principal can see in the workspace. Users can select any endpoint from that list.

The `serving_endpoint` variable in `databricks.yml` grants the app's service principal `CAN_QUERY` on one specific endpoint:

```yaml
variables:
  serving_endpoint:
    default: "databricks-claude-sonnet-4-5"
```

**For custom endpoints**, only the endpoint named here is guaranteed to be callable. If users select a different custom endpoint from the dropdown and the SP doesn't have `CAN_QUERY` on it, calls will fail. To grant access to additional custom endpoints, add more resource entries:

```yaml
resources:
  apps:
    prompt_playground:
      resources:
        - name: serving-endpoint
          serving_endpoint:
            name: databricks-claude-sonnet-4-5
            permission: CAN_QUERY
        - name: my-custom-endpoint
          serving_endpoint:
            name: my-custom-endpoint
            permission: CAN_QUERY
```

### 6. Validate the configuration

```bash
databricks bundle validate
```

Fix any errors before continuing.

### 7. Deploy

```bash
# Deploy to dev (default)
databricks bundle deploy

# Deploy to prod
databricks bundle deploy -t prod
```

### 8. Start the app

```bash
# Start in dev
databricks bundle run prompt_playground

# Start in prod
databricks bundle run prompt_playground -t prod
```

The app URL will be printed in the output. You can also find it in your workspace under **Compute > Apps**.

### 9. Verify the deployment

```bash
databricks bundle summary
```

---

## Register Your First Prompt

**Option A — from within the app (no code):**

1. Open the Prompt Playground app
2. Click the **+** icon next to the Prompt selector
3. Fill in a name, optional description, and template (use `{{variable}}` placeholders)
4. Click **Create Prompt** — the new prompt is registered and immediately selected

**Option B — from a notebook or the MLflow UI:**

```python
import mlflow

mlflow.set_registry_uri("databricks-uc")

mlflow.register_prompt(
    name="your_catalog.prompts.my_prompt",
    template="You are a helpful assistant. Answer: {{question}}",
    commit_message="Initial version",
)
```

Then open the app and select your prompt from the dropdown.

> **Editing templates in-app:** Select a prompt and version, then click the **+ New version** button to open the editor. Saving registers a new version automatically.

---

## Troubleshooting

**App fails to start / "MANAGE privilege" error**
→ The service principal is missing `MANAGE` on the prompts schema. Run the SQL grants in the section above.

**"No prompts found"**
→ Check that `PROMPT_CATALOG` and `PROMPT_SCHEMA` in `src/app.yaml` match where your prompts are registered, and that the service principal has access.

**Eval datasets not loading**
→ Verify `EVAL_SCHEMA` in `src/app.yaml` and that the service principal has `SELECT` on that schema.

**Model endpoint not listed**
→ The endpoint may not be in `READY` state. Check **Serving > Endpoints** in your workspace.

---

## How to get help

For questions or issues, please open a GitHub issue and the team will respond on a best effort basis.

---

## License

This project is licensed under the [Databricks DB License](LICENSE.md).
