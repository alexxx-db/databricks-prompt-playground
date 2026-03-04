# CHANGELOG

## 0.5.0 (2026-03-03)

### Features

- **In-App Configuration UI**: Added slide-over Settings panel (gear icon in header) for configuring SQL warehouse, Prompt Registry catalog/schema, and Eval catalog/schema via searchable dropdowns — no YAML or environment variable edits required
- **App-Wide Experiment Filter**: Added header-level MLflow experiment selector that applies across all tabs
- **Eval Abort**: Added ability to cancel a running evaluation mid-flight from the UI

### Improvements

- Catalog and schema configuration moved out of Prompts and Evaluate panels into the Settings panel
- Prompts and Evaluate tab left panels now show active `catalog.schema` badge with an "Edit →" shortcut to Settings, and a setup CTA when unconfigured
- `SearchableSelect` component gains lazy-load-on-open callback and loading spinner state
- Settings persisted server-side in `pp_settings.json`; env var defaults merged with persisted values so self-hosted and Marketplace deploys both work

---

## 0.4.0 (2026-03-02)

### Features

- **Persistent Open in Databricks Button**: Added always-visible link in the tab bar to the active workspace

### Improvements

- Evaluate tab UX overhaul with 10 improvements to dataset selection, column mapping, judge configuration, and results display

---

## 0.3.0 (2026-03-01)

### Features

- **3-Tab Restructure**: Navigation reorganized into Prompts / Playground / Evaluate. Prompts tab has a fixed registry+experiment selector, flex-grow version list, sticky "Test in Playground →" footer, and full-height prompt preview. Playground tab shows a loaded-prompt indicator, variable inputs, model selector, and run controls. Evaluate left panel has three sections separated by dividers
- **System/User Prompt Splitting**: Prompts using `<system>...</system><user>...</user>` XML convention are parsed and rendered as separate panels in the Playground tab, with system and user content tracked independently
- **Chat UI**: Messages displayed in chat bubble layout when a prompt contains a system/user split
- **Eval Dataset Preview**: Added `GET /api/eval/table-preview` endpoint and collapsible `TablePreview` component in EvaluatePanel showing column names and row counts before running
- **Unfilled Variable Validation**: Added amber warning banner in Run Controls when template variables have no value, blocking accidental runs with unfilled `{{variable}}` placeholders

### Improvements

- Added 120-second timeout to all `call_model()` calls to prevent hung requests
- Added `{{ trace }}` and `{{ expectations }}` as built-in variables available in judge prompt templates

---

## 0.2.0 (2026-02-28)

### Features

- **System/User Prompt Splitting**: Initial implementation of `<system>/<user>` XML convention for splitting prompt templates into system and user components
- **Eval Preview**: Added preview of eval dataset contents before committing to a run
- **Version Descriptions**: Prompt versions can carry a description shown in the version card list

---

## 0.1.0 (2026-02-27)

Initial version of Prompt Playground
