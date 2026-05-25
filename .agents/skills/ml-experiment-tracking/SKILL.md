---
name: ml-experiment-tracking
description: >
  Use this skill when setting up, debugging, or extending MLflow tracking in any ML
  repo — tracking URI resolution, run lifecycle (local vs Azure ML compute),
  metric and parameter logging, experiment naming, model registration, or querying
  past runs. Also use when MLflow calls are failing or producing duplicate/nested runs.
  Do NOT use for reading model performance results for deployment decisions (use
  ml-evaluation) or for running training (use ml-model-development). Trigger on:
  "log metrics", "MLflow not working", "set up experiment", "register model",
  "query runs", "compare experiments", "mlflow.start_run", or any Azure ML + MLflow
  integration question — even if the user does not say "MLflow" explicitly.
compatibility: opencode
metadata:
  stage: experiment-tracking
  repos: <your-repo-name>
---

# ML Experiment Tracking Skill

## When to load this skill
Load when the task involves: logging metrics or parameters to MLflow, setting up experiments, querying run results, comparing runs, registering models, or debugging MLflow integration issues.

---

## Gotchas

- **The MLflow tracking URI is not in any environment variable.** It must be fetched at runtime from `ml_client.workspaces.get(workspace_name).mlflow_tracking_uri`. Hard-coding it or reading it from an env var will break across workspace environments.
- **Azure ML auto-manages runs on compute — `mlflow.start_run()` creates a nested run.** When `AZUREML_RUN_ID` is set, a run is already active. Calling `start_run()` creates a child run, not a top-level run. Always check `is_azure_ml_environment()` before starting a run.
- **`mlflow.active_run()` returns `None` after `mlflow.end_run()`.** Calling `start_run()` again after ending a run creates a new run with a new ID, breaking continuity in the experiment. Use the `should_manage_run` guard pattern — start once, end once, in a `finally` block.
- **Use `mlflow.lightgbm.log_model`, not `mlflow.sklearn.log_model` for LightGBM.** The sklearn flavour strips LightGBM-native metadata. AML endpoints loading a sklearn-flavoured LightGBM model may fail or lose feature name information.
- **AML model version strings use the `v` prefix.** Version `1` is stored as `"v1"`. When parsing programmatically: `.replace("v", "").replace("-", "")` before casting to int.

---

## Critical: azureml-mlflow vs standalone mlflow

These repos use `azureml-mlflow`, not standalone MLflow. The tracking URI is **not** a static env var — it is fetched from the AML workspace at runtime:

```python
import mlflow
from azure.ai.ml import MLClient

mlflow_tracking_uri = ml_client.workspaces.get(workspace_name).mlflow_tracking_uri
mlflow.set_tracking_uri(mlflow_tracking_uri)
```

For local CLI queries:
```bash
az ml workspace show \
  --name <workspace> \
  --resource-group <rg> \
  --query mlflowTrackingUri -o tsv
```

---

## Run lifecycle — local vs Azure ML

**Do NOT** unconditionally start/end runs. Azure ML auto-manages runs when running on compute:

```python
import os

def is_azure_ml_environment() -> bool:
    """Check if running in Azure ML compute."""
    return any(os.environ.get(v) for v in [
        "AZUREML_RUN_ID", "AZUREML_EXPERIMENT_ID",
        "AZUREML_RUN_TOKEN", "AZUREML_SERVICE_ENDPOINT",
    ])

# Correct pattern
active_run = mlflow.active_run()
should_manage_run = active_run is None and not is_azure_ml_environment()

if should_manage_run:
    mlflow.start_run(run_name=f"{model_name}_training")

try:
    # ... training code ...
    mlflow.log_param("model_type", model_name)
    mlflow.log_metric("test_r2", test_r2)
except Exception as e:
    logger.warning(f"MLflow logging failed: {e}")  # Never let MLflow failures stop training

finally:
    if should_manage_run and mlflow.active_run():
        mlflow.end_run()
```

**Always wrap MLflow calls in try/except** — a broken tracking connection must not abort training.

---

## What to log per run

### All repos
```python
mlflow.log_param("model_type", model_name)
mlflow.log_param("train_size", len(X_train))
mlflow.log_param("test_size", len(X_test))
mlflow.log_param("n_features", X_train.shape[1])
```

### Classification
```python
mlflow.log_metric("roc_auc", roc_auc)
mlflow.log_metric("fbeta", fbeta)
mlflow.log_metric("precision", precision)
mlflow.log_metric("recall", recall)
mlflow.log_metric("threshold", optimal_threshold)
```

### Regression
```python
mlflow.log_metric("train_mae", train_mae)
mlflow.log_metric("train_r2", train_r2)
mlflow.log_metric("test_mae", test_mae)
mlflow.log_metric("test_r2", test_r2)
mlflow.log_metric("test_mape", test_mape)
# For multi-target: prefix with target name
mlflow.log_metric("target_a_test_r2", r2)
```

---

## Experiment naming conventions

Experiment names should follow a consistent pattern for your use-case. Define them in `docs/experiment-conventions.md`. Example pattern: `<usecase>-training`, `<usecase>-training_calibration`.

Set experiment before starting run:
```python
experiment = mlflow.get_experiment_by_name(experiment_name)
if experiment is None:
    mlflow.create_experiment(experiment_name)
else:
    mlflow.set_experiment(experiment_name)
```

---

## Model registration

```python
import mlflow.sklearn  # or mlflow.lightgbm

# Log model artifact
mlflow.lightgbm.log_model(model, artifact_path="model")

# Register in AML model registry
model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
registered = mlflow.register_model(model_uri, name=f"{model_name}_v{version}")
```

Model naming format: `{model_name}_v{version}` (e.g., `my_usecase_model_v1`).

---

## Querying runs

Use the `run_mlflow_query` tool, or:
```python
from mlflow.tracking import MlflowClient

client = MlflowClient()
runs = client.search_runs(
    experiment_ids=[experiment.experiment_id],
    order_by=["metrics.test_r2 DESC"],
    max_results=10,
)
for run in runs:
    print(run.info.run_id, run.data.metrics.get("test_r2"))
```

---

## Evaluation criteria

Before handing off experiment tracking code, verify all of the following:

- [ ] Tracking URI fetched from `ml_client.workspaces.get(workspace_name).mlflow_tracking_uri` — not hardcoded, not from env var
- [ ] `is_azure_ml_environment()` check used before calling `mlflow.start_run()` — Azure ML auto-manages runs
- [ ] `mlflow.active_run()` checked before starting a new run to avoid nested run errors
- [ ] All MLflow logging calls wrapped in `try/except Exception as e` with `logger.warning` — tracking failure must not abort training
- [ ] `mlflow.end_run()` only called when `should_manage_run` is True and in a `finally` block
- [ ] Experiment name follows conventions defined in `docs/experiment-conventions.md`
- [ ] All required params logged: `model_type`, `train_size`, `test_size`, `n_features`
- [ ] Problem-appropriate metrics logged (AUC+fbeta for classification; MAE+R²+MAPE for regression; multi-target metrics prefixed with target name)
- [ ] Model registered with naming format `{model_name}_v{version}`
- [ ] `mlflow.lightgbm.log_model` (or appropriate flavour) used — not `mlflow.sklearn.log_model` for LightGBM
