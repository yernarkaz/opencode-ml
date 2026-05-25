---
description: Launch a model training run. Usage: /train <config_or_args>
---

# Start a model training pipeline run with: $ARGUMENTS

Current repo: !`pwd`
Git branch: !`git branch --show-current 2>/dev/null`
Active conda/uv environment: !`python --version 2>/dev/null`
Recent MLflow experiments: !`python -c "import mlflow; [print(e.name, e.experiment_id) for e in mlflow.search_experiments()]" 2>/dev/null || echo "MLflow not reachable locally"`

Before running training:

1. Verify `PYTHONPATH` includes `aml/pipeline/src` (injected automatically by ml-env plugin)
2. Check that component YAML arguments are in sync with ArgumentParser definitions:
   
   ```
   pytest tests/integration/test_component_argument_validation.py -v
   ```
   
   If this test does not exist, note it and skip.
3. Confirm the target column, date column, and experiment name from the arguments provided
4. Run the training script with `--local_compute True` if running locally

After training completes:
5. Report the MLflow run ID, experiment name, and key metrics (AUC/F-beta for classification; MAE/R² for regression)
6. Remind: run `pytest tests/unit/ --verbose --tb=short` before committing

Refer to `docs/experiment-conventions.md` for experiment naming and MLflow URI conventions.
