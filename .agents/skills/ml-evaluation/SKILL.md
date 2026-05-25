---
name: ml-evaluation
description: >
  Use this skill when computing, reviewing, or comparing model metrics for any ML
  repo — AUC, F-beta, MAE, R², MAPE, calibration gaps, residual analysis, or the
  pre-deployment gate checklist. Also use when deciding whether a model is ready to
  promote from D to Q or from Q to P. Do NOT use for setting up MLflow logging
  (use ml-experiment-tracking) or for running training (use ml-model-development).
  Trigger on: "evaluate the model", "check metrics", "is this good enough to deploy",
  "overfitting check", "calibration", "residuals", "compare runs", "acceptance
  thresholds", or any mention of roc_auc, avg_average_precision, R², or MAPE in
  the context of validating model outputs.
compatibility: opencode
metadata:
  stage: evaluation
  repos: <your-repo-name>
---

# ML Evaluation Skill

## When to load this skill
Load when the task involves: computing model metrics, comparing runs, diagnosing overfitting, checking calibration, validating predictions before deployment, or writing evaluation code.

---

## Gotchas

- **Always evaluate on original scale (after `expm1`), never on log-transformed values.** Evaluating log-transformed regression predictions produces inflated R² scores (often 0.95+) that have no meaning for stakeholders. Always inverse-transform before computing any metric.
- **`mean_absolute_percentage_error` returns `inf` on zero targets.** Apply `mask = y_true > 0` before computing MAPE. This is already shown in the template — do not remove the mask.
- **`r2_score` returning a negative value is correct, not a bug.** A negative R² means the model is worse than simply predicting the mean. Do not clip it or treat it as zero.
- **Acceptance thresholds are promotion gates, not quality targets.** A model that just clears the minimum R² bar is not necessarily ready for production — it only clears the minimum for promotion to QA. Always investigate models near the threshold before P promotion.
- **Calibration gap check uses predicted probability mean, not threshold-based predicted rate.** The check is `abs(y_prob.mean() - y_true.mean())`, not `abs(y_pred.mean() - y_true.mean())`. Using the hard-prediction rate gives a meaningless result at a different threshold.

---

## Three canonical evaluation templates

---

### Template 1 — Binary classification

**Primary metric**: ROC-AUC (optimised during hyperparameter search)
**Deployment metric**: F-beta at the optimal risk threshold

```python
from sklearn.metrics import (
    roc_auc_score, fbeta_score, precision_score,
    recall_score, confusion_matrix, classification_report,
)
import numpy as np

def evaluate_classifier(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    beta: float = 2.0,
    threshold: float = 0.5,
) -> dict:
    """Evaluate binary classifier with AUC, F-beta, and confusion matrix.

    Args:
        y_true: True binary labels.
        y_prob: Predicted probabilities for the positive class.
        beta: Beta for F-beta score (beta>1 favours recall).
        threshold: Decision threshold.

    Returns:
        Dictionary of evaluation metrics.
    """
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "roc_auc": roc_auc_score(y_true, y_prob),
        "fbeta": fbeta_score(y_true, y_pred, beta=beta),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn),
        "positive_rate": float(y_true.mean()),
        "predicted_rate": float(y_pred.mean()),
        "threshold": threshold,
    }
```

**Overfitting signal**: train AUC - test AUC > 0.05
**Calibration check**: predicted probability mean should approximate actual positive rate

```python
# Calibration check
prob_mean = y_prob.mean()
actual_rate = y_true.mean()
calibration_gap = abs(prob_mean - actual_rate)
if calibration_gap > 0.05:
    print(f"WARNING: Calibration gap {calibration_gap:.3f} — consider Platt scaling or isotonic regression")
```

---

### Template 2 — Single-target log regression

**Primary metrics**: MAE, R², MAPE, correlation

```python
from sklearn.metrics import mean_absolute_error, r2_score, mean_absolute_percentage_error
import numpy as np

def evaluate_regressor(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    label: str = "",
) -> dict:
    """Evaluate regression model predictions.

    Args:
        y_true: True target values (original scale, not log).
        y_pred: Predicted values (original scale, not log).
        label: Optional label prefix for metric keys.

    Returns:
        Dictionary of evaluation metrics.
    """
    prefix = f"{label}_" if label else ""
    mask = y_true > 0  # exclude zeros for MAPE
    return {
        f"{prefix}mae": mean_absolute_error(y_true, y_pred),
        f"{prefix}r2": r2_score(y_true, y_pred),
        f"{prefix}mape": mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100,
        f"{prefix}correlation": float(np.corrcoef(y_true, y_pred)[0, 1]),
        f"{prefix}residual_mean": float((y_true - y_pred).mean()),
        f"{prefix}residual_std": float((y_true - y_pred).std()),
    }
```

**Overfitting signal**: train R² - test R² > 0.05
**Systematic bias check**: residual mean should be near zero

```python
residuals = y_true - y_pred
if abs(residuals.mean()) > 0.1 * y_true.mean():
    print(f"WARNING: Systematic bias detected — mean residual = {residuals.mean():.2f}")
```

---

### Template 3 — Multi-target log regression

```python
def evaluate_multi_output(
    y_true: np.ndarray,    # shape (n_samples, n_targets)
    y_pred: np.ndarray,    # shape (n_samples, n_targets)
    target_cols: list,
) -> dict:
    """Evaluate multi-output regression for all targets.

    Args:
        y_true: True target values, shape (n_samples, n_targets).
        y_pred: Predicted values, shape (n_samples, n_targets).
        target_cols: List of target column names.

    Returns:
        Nested dictionary of per-target metrics.
    """
    results = {}
    for i, col in enumerate(target_cols):
        results[col] = evaluate_regressor(y_true[:, i], y_pred[:, i], label=col)
    return results
```

**Acceptance thresholds**: define per-target gates in your `docs/program.md`. Flag any target below threshold as underperforming before deployment.

---

## Pre-deployment evaluation gate

Run this checklist before promoting a model to Q or P:

- [ ] Test metrics meet acceptance thresholds (see above)
- [ ] Train/test metric gap within tolerance (no overfitting)
- [ ] Predictions are non-null and within expected range
- [ ] No negative predictions (clips applied correctly)
- [ ] Sample payload test through the endpoint returns correct schema
- [ ] MLflow run ID recorded and model registered in AML registry

---

## Residual analysis (regression)

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# Predicted vs actual
axes[0].scatter(y_true, y_pred, alpha=0.3, s=5)
axes[0].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], "r--")
axes[0].set_xlabel("Actual")
axes[0].set_ylabel("Predicted")
axes[0].set_title("Predicted vs Actual")

# Residuals
residuals = y_true - y_pred
axes[1].hist(residuals, bins=50)
axes[1].axvline(0, color="r", linestyle="--")
axes[1].set_title(f"Residuals (mean={residuals.mean():.2f}, std={residuals.std():.2f})")

plt.tight_layout()
plt.savefig("evaluation-plots/residuals.png", dpi=150)
```

---

## Evaluation criteria

Before handing off evaluation code or results, verify all of the following:

- [ ] Correct template used for the problem type: `evaluate_classifier` (binary), `evaluate_regressor` (regression), `evaluate_multi_output` (multi-target)
- [ ] Metrics computed on **original scale** (after `expm1` inverse transform) — not on log-transformed values
- [ ] Train/test metric gap checked against overfitting threshold (AUC gap > 0.05 for classification; R² gap > 0.05 for regression)
- [ ] Calibration gap checked for binary classifiers (`abs(prob_mean - actual_rate) > 0.05` triggers warning)
- [ ] Systematic bias checked for regression (`abs(residuals.mean()) > 0.1 * y_true.mean()` triggers warning)
- [ ] Per-target acceptance thresholds verified for multi-target regression (as defined in `docs/program.md`)
- [ ] Predictions are non-null and non-negative (clips confirmed applied)
- [ ] Residual plots saved to `evaluation-plots/residuals.png`
- [ ] Pre-deployment gate checklist completed in full before any promotion to Q or P
- [ ] MLflow run ID recorded and model registered before checklist sign-off
