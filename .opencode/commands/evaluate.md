---
description: Evaluate a trained model run. Usage: /evaluate <run_id>
---

# Evaluate MLflow run: $ARGUMENTS

Current repo: !`pwd`
Git branch: !`git branch --show-current 2>/dev/null`

Use the `run-mlflow-query` tool to fetch all logged metrics and parameters for the given run ID.

Then produce a structured evaluation report:

## For binary classification

- ROC-AUC (primary optimisation metric)
- F-beta score at the chosen threshold
- Confusion matrix breakdown (TP, FP, TN, FN)
- Precision / recall / F1
- Compare train vs test metrics — flag if gap > 5% (overfitting signal)
- Check calibration: predicted probability distribution vs actual positive rate

## For single-target regression

- MAE, R², MAPE, correlation
- Residual distribution: mean, std, skew
- Compare train vs test R² — flag if gap > 0.05
- Check for systematic bias: predicted vs actual scatter

## For multi-target regression

- Per-target metrics: MAE, R², MAPE for each target
- Flag any target with R² < 0.5 as underperforming
- Check prediction caps were applied (no negative or zero predictions)

## All use-cases

- List all logged hyperparameters
- List all logged artifacts
- Compare against previous best run if available
- Recommend next experiment direction based on findings

Refer to `docs/experiment-conventions.md` for run naming and tracking URI conventions (if populated for your use-case).
