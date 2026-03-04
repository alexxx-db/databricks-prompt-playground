# Prompt Playground

Prompt Playground is an interactive, no-code Databricks App for designing, testing, and evaluating prompts stored in the [Prompt Registry](https://docs.databricks.com/aws/en/mlflow3/genai/prompt-version-mgmt/prompt-registry/). It enables product owners, prompt engineers, and both technical and non-technical users to iterate on prompt templates, run them against live model serving endpoints, and evaluate quality at scale — without writing code.

- **Manage prompts** — browse, create, and version prompt templates directly from the UI
- **Iterate interactively** — fill in `{{template_variables}}`, run against any model serving endpoint, and preview the fully rendered prompt before executing
- **Evaluate at scale** — run a prompt version against any Unity Catalog Delta table, score with built-in LLM-as-judge presets or custom judges, and triage low-scoring results in-app
- **Tightly integrated with Databricks** — every run and evaluation is logged as an MLflow trace with direct links to the Experiments UI; all data stays in your Unity Catalog environment

## Installation

### Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install.html) `>= 0.220.0`, authenticated via `databricks auth login`
- A **SQL Warehouse** running in your workspace
- A **model serving endpoint** — [Foundation Model API](https://docs.databricks.com/machine-learning/foundation-models/index.html) endpoints work out of the box
- The app's **service principal** must have `MANAGE` on the Unity Catalog schema where your prompts are stored, and `MANAGE` on the schema where eval results will be written

### Setup

**1. Clone the repository**

```bash
git clone https://github.com/databricks-solutions/prompt-playground.git
cd prompt-playground
```

**2. Deploy**

```bash
databricks bundle validate
databricks bundle deploy
databricks bundle run prompt_playground
```

The app URL will be printed in the output. You can also find it under **Compute > Apps** in your workspace.

## Usage

> **First time? Start here:** Open the app and check out the **How to Use** tab for a full walkthrough. Click the **Settings** icon in the upper right to configure your SQL Warehouse, prompt catalog/schema, and evaluation dataset catalog/schema.

**Register your first prompt from within the app:**

1. Open the Prompt Playground app
2. Click the **+** icon next to the Prompt selector
3. Fill in a name, optional description, and template (use `{{variable}}` placeholders)
4. Click **Create Prompt** — the new prompt is registered and immediately selected

## Troubleshooting

**App fails to start / "MANAGE privilege" error**
→ The service principal is missing `MANAGE` on the prompts schema.

**"No prompts found"**
→ Open Settings (upper right) and verify your prompt catalog and schema are correct. Confirm the app's service principal has access to that schema.

**Eval datasets not loading**
→ Open Settings and verify your evaluation dataset catalog and schema. Confirm the service principal has `MANAGE` on that schema.

**Model endpoint not listed**
→ The endpoint may not be in `READY` state. Check **Serving > Endpoints** in your workspace.

## How to get help

For questions or bugs, please contact agents-outreach@databricks.com and the team will reach out shortly.

## License

This project is licensed under the [Databricks DB License](LICENSE.md).

| library | description | license | source |
|---------|-------------|---------|--------|
| React | Frontend framework | MIT | https://github.com/facebook/react |
| FastAPI | Backend web framework | MIT | https://github.com/tiangolo/fastapi |
| Tailwind CSS | Utility-first CSS | MIT | https://github.com/tailwindlabs/tailwindcss |
| Vite | Frontend build tool | MIT | https://github.com/vitejs/vite |
| MLflow | ML lifecycle management | Apache 2.0 | https://github.com/mlflow/mlflow |
| Lucide React | Icon library | ISC | https://github.com/lucide-icons/lucide |
