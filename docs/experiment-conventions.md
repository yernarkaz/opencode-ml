# Experiment Conventions — `<FILL IN: repository name>`

> **Template** — Replace every `<FILL IN>` placeholder with values specific to your use-case.
> Delete guidance text in square brackets `[...]` once filled.

---

## Experiment Naming Convention

```
<repo>_<model>_<date>_<variant>
```

| Segment | Example | Notes |
|---------|---------|-------|
| `<repo>` | `<FILL IN: e.g. churn-pred>` | Short, lowercase, hyphenated |
| `<model>` | `<FILL IN: e.g. lgbm, catboost, xgb>` | Model family identifier |
| `<date>` | `<FILL IN: e.g. 20250610>` | `YYYYMMDD` format |
| `<variant>` | `<FILL IN: e.g. v1, optuna-r1, no-embeddings>` | Descriptive tag for the run variant |

**Full example:** `<FILL IN: e.g. churn-pred_lgbm_20250610_optuna-r1>`

---

## MLflow Tracking

- **Tracking URI resolution:** Always fetched dynamically from the Azure ML workspace client. Never hardcoded.

  ```python
  mlflow_tracking_uri = azure_manager._ml_client.workspaces.get(
      config.ml_workspace_name
  ).mlflow_tracking_uri
  mlflow.set_tracking_uri(mlflow_tracking_uri)
  ```

- **Run lifecycle on AML compute:** Do NOT call `mlflow.start_run()` or `mlflow.end_run()` when `AZUREML_RUN_ID` is set — the run is managed by the pipeline.

  ```python
  if not os.environ.get("AZUREML_RUN_ID"):
      if not mlflow.active_run():
          mlflow.start_run()
  ```

---

## Metric Logging Conventions

| Metric | Logged at | Description |
|--------|-----------|-------------|
| `<FILL IN: e.g. train_<metric>` | End of training | `<FILL IN: metric computed on training fold>` |
| `<FILL IN: e.g. test_<metric>` | End of evaluation | `<FILL IN: metric computed on held-out test set>` |
| `<FILL IN: e.g. fold_<N>_<metric>` | Per-fold | `<FILL IN: per-fold metric for temporal CV>` |
| `<FILL IN: e.g. calibration_brier_score>` | Post-training | `<FILL IN: calibration check, if applicable>` |
| `<FILL IN: e.g. training_duration_seconds>` | End of run | `<FILL IN: wall-clock training time>` |

---

## Acceptance Thresholds

| Metric | D → Q threshold | Q → P threshold |
|--------|-----------------|-----------------|
| `<FILL IN: e.g. roc_auc>` | `<FILL IN: e.g. >= 0.75>` | `<FILL IN: e.g. >= 0.80>` |
| `<FILL IN: e.g. f2_score>` | `<FILL IN>` | `<FILL IN>` |
| `<FILL IN: e.g. mape>` | `<FILL IN: e.g. <= 15%>` | `<FILL IN: e.g. <= 10%>` |
| `<FILL IN: e.g. calibration_gap>` | `<FILL IN: e.g. <= 0.05>` | `<FILL IN: e.g. <= 0.03>` |

---

## Temporal Split Pattern

| Split | Date range / ratio | Description |
|-------|--------------------|-------------|
| **Train** | `<FILL IN: e.g. offset_date <= 2024-01-01 (70%)>` | `<FILL IN: primary training window>` |
| **Validation** | `<FILL IN: e.g. 2024-01-02 to 2024-04-01 (15%)>` | `<FILL IN: hyperparameter tuning / early stopping>` |
| **Test** | `<FILL IN: e.g. offset_date >= 2024-04-02 (15%)>` | `<FILL IN: held-out evaluation; never used in training>` |

> **Rule:** Splits are strictly chronological by `offset_date`. No shuffling. No data from validation or test periods leaks into training features.

---

## Model Naming Format

Registered models in the MLflow model registry follow:

```
<repo>_<model_family>_<date>_<variant>
```

| Segment | Example |
|---------|---------|
| `<repo>` | `<FILL IN: e.g. churn-pred>` |
| `<model_family>` | `<FILL IN: e.g. lgbm>` |
| `<date>` | `<FILL IN: e.g. 20250610>` |
| `<variant>` | `<FILL IN: e.g. optuna-r1>` |

**Full example:** `<FILL IN: e.g. churn-pred_lgbm_20250610_optuna-r1>`

---

## Deployment Environments

| Environment | Abbreviation | Workspace name | Description |
|-------------|--------------|----------------|-------------|
| Development | **D** | `<FILL IN: e.g. ml-ws-churn-dev>` | `<FILL IN: training and experimentation workspace>` |
| QA | **Q** | `<FILL IN: e.g. ml-ws-churn-qa>` | `<FILL IN: pre-deployment validation; mirrors prod config>` |
| Production | **P** | `<FILL IN: e.g. ml-ws-churn-prod>` | `<FILL IN: live scoring endpoint; restricted access>` |

**Promotion path:** D → Q → P. A model must pass Q acceptance thresholds before promotion to P.
