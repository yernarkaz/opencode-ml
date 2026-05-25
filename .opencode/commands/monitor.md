---
description: Check model monitoring status and set up monitoring for a deployed endpoint. Usage: /monitor <endpoint_name>
---

# Check or configure model monitoring for endpoint: $ARGUMENTS

Current repo: !`pwd`
Azure CLI login status: !`az account show --query "{subscription:name, user:user.name}" -o table 2>/dev/null || echo "Not logged in — run: az login"`

## Monitoring status check

1. List active monitoring schedules:
   
   ```bash
   az ml schedule list --workspace-name <ws> --resource-group <rg> --query "[?properties.action.job_definition.component contains 'monitor']"
   ```

2. Check recent monitoring run results in MLflow — look for data drift and model performance signals

## Monitoring setup (if not configured)

If a monitoring pipeline script exists in the repo (e.g. `setup_model_monitoring.py`), run it with:

```bash
python aml/pipeline/src/setup_model_monitoring.py \
  --endpoint_name <endpoint> \
  --workspace_name <ws> \
  --resource_group <rg>
```

## Drift thresholds (recommended defaults)

| Signal                   | Metric                     | Alert threshold |
| ------------------------ | -------------------------- | --------------- |
| Data drift (numerical)   | Jensen-Shannon distance    | > 0.15          |
| Data drift (numerical)   | Population Stability Index | > 0.25          |
| Data drift (numerical)   | KS test p-value            | < 0.05          |
| Data drift (categorical) | Chi-squared p-value        | < 0.05          |
| Data drift (categorical) | Jensen-Shannon distance    | > 0.15          |

## Model performance signals to check

- Prediction distribution shift vs training baseline
- Feature attribution drift (top-10 features by importance)
- Data quality: null rate increase, unexpected value ranges

## Recommended actions on drift detection

1. Inspect which features are drifting — use feature attribution signal
2. Check upstream ADF pipeline for source data changes
3. If drift is sustained > 2 weeks: trigger retraining pipeline
4. Document finding in the relevant issue tracker ticket

Refer to `docs/experiment-conventions.md` for MLflow tracking URI and experiment naming (if populated for your use-case).
