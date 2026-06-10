---
name: sklearn-model-trainer
description: >
  Use this skill when training scikit-learn models (RandomForest, GradientBoosting, linear models, SVM, KNN)
  in Azure ML pipelines. Trigger on: "sklearn", "scikit-learn", "RandomForest", "GradientBoosting",
  "linear regression", "logistic regression", "SVM", "KNN", or any mention of sklearn models.
  Do NOT use for LightGBM/CatBoost (use ml-model-development) or deep learning (use deep-learning-optimizer).
compatibility: opencode
metadata:
  stage: model-development
  repos: <your-repo-name>
---

# Scikit-learn Model Trainer Skill

## When to load this skill
Load when the task involves training scikit-learn models in Azure ML pipelines — RandomForest, GradientBoosting, linear models (LinearRegression, LogisticRegression, Ridge, Lasso), SVM/SVR, KNN, or any sklearn-based model development. Do NOT use for LightGBM or CatBoost (use ml-model-development skill) or deep learning frameworks (use deep-learning-optimizer skill).

---

## Training workflow

### Step 1 — Model selection based on problem type

**Classification**
| Dataset size | Recommended model | Rationale |
|---|---|---|
| Small (< 10K rows) | LogisticRegression, SVC | Fast, interpretable, strong baselines |
| Medium (10K–500K) | RandomForestClassifier, GradientBoostingClassifier | Handles nonlinearity, robust |
| Large (> 500K) | GradientBoostingClassifier, HistGradientBoostingClassifier | Hist variant is memory-efficient |

**Regression**
| Dataset size | Recommended model | Rationale |
|---|---|---|
| Small (< 10K rows) | LinearRegression, Ridge | Simple baseline, interpretable |
| Medium (10K–500K) | RandomForestRegressor, GradientBoostingRegressor | Nonlinear relationships |
| Large (> 500K) | HistGradientBoostingRegressor | Memory-efficient, handles categoricals |

**Quick selection heuristic**
```python
# Start with a strong baseline
from sklearn.ensemble import HistGradientBoostingClassifier  # or Regressor
model = HistGradientBoostingClassifier(random_state=42)
```

### Step 2 — Cross-validation setup (temporal split, NOT random KFold)

For temporal datasets, random KFold introduces leakage. Use `TimeSeriesSplit` or a custom temporal splitter:

```python
from sklearn.model_selection import TimeSeriesSplit

# Temporal CV — respects time ordering
tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
    # train and evaluate...
```

For per-row `offset_date` datasets, implement a custom splitter that respects each row's cutoff:

```python
def temporal_split(df, offset_date_col, train_ratio=0.8):
    """Split respecting per-row offset_date."""
    cutoff = df[offset_date_col].quantile(train_ratio)
    train_mask = df[offset_date_col] < cutoff
    return df[train_mask], df[~train_mask]
```

### Step 3 — Hyperparameter tuning grid

**RandomForest**
```python
param_grid = {
    "n_estimators": [100, 200, 500],
    "max_depth": [5, 10, 20, None],
    "min_samples_split": [2, 5, 10],
    "min_samples_leaf": [1, 2, 4],
    "max_features": ["sqrt", "log2", None],
}
```

**GradientBoosting**
```python
param_grid = {
    "n_estimators": [100, 200, 500],
    "learning_rate": [0.01, 0.05, 0.1],
    "max_depth": [3, 5, 8],
    "subsample": [0.8, 1.0],
    "min_samples_leaf": [5, 10, 20],
}
```

**LogisticRegression**
```python
param_grid = {
    "C": [0.01, 0.1, 1.0, 10.0],
    "penalty": ["l1", "l2"],
    "solver": ["liblinear", "saga"],
}
```

**SVM/SVC**
```python
param_grid = {
    "C": [0.1, 1.0, 10.0],
    "gamma": ["scale", "auto", 0.01, 0.1],
    "kernel": ["rbf", "linear"],
}
```

Use `RandomizedSearchCV` for large grids (faster than exhaustive GridSearchCV):
```python
from sklearn.model_selection import RandomizedSearchCV

search = RandomizedSearchCV(
    estimator=model,
    param_distributions=param_grid,
    n_iter=50,
    cv=tscv,
    scoring="roc_auc",
    n_jobs=-1,
    random_state=42,
)
search.fit(X_train, y_train)
```

### Step 4 — Model evaluation and comparison

```python
from sklearn.metrics import (
    roc_auc_score, f1_score, accuracy_score,
    mean_absolute_error, r2_score, mean_absolute_percentage_error,
)
import mlflow

# Classification metrics
y_pred = best_model.predict(X_val)
y_proba = best_model.predict_proba(X_val)[:, 1]

metrics = {
    "roc_auc": roc_auc_score(y_val, y_proba),
    "f1": f1_score(y_val, y_pred),
    "accuracy": accuracy_score(y_val, y_pred),
}

# Regression metrics
y_pred = best_model.predict(X_val)
metrics = {
    "r2": r2_score(y_val, y_pred),
    "mae": mean_absolute_error(y_val, y_pred),
    "mape": mean_absolute_percentage_error(y_val, y_pred),
}

# Log to MLflow
for name, value in metrics.items():
    mlflow.log_metric(name, value)
```

For regression with log-transformed targets, **always invert the transform before computing metrics**:
```python
import numpy as np

# If training on log1p(target), invert predictions before evaluation
pred_original = np.expm1(model.predict(X_val))
pred_original = np.where(pred_original < 0, 0.00001, pred_original)
mae = mean_absolute_error(y_val, pred_original)
```

### Step 5 — Model serialization and inference integration

```python
import joblib

# Serialize with joblib (preferred over pickle for sklearn)
model_path = os.path.join(output_dir, "model.joblib")
joblib.dump(best_model, model_path)

# Also save preprocessing artifacts if applicable
joblib.dump(preprocessor, os.path.join(output_dir, "preprocessor.joblib"))

# Upload to MLflow as artifact
mlflow.log_artifact(model_path)
```

In the inference pipeline (`inference_model.py`), load and score:
```python
model = joblib.load(model_path)
predictions = model.predict(X_inference)
```

---

## Gotchas

- **sklearn models do NOT handle categorical features natively.** Encode categoricals before training — use `OneHotEncoder`, `OrdinalEncoder`, or `category_encoders` (target encoding, binary encoding). Do NOT pass raw string columns to sklearn estimators.
- **Temporal CV is mandatory for time-series data.** Random KFold splits introduce future-to-past leakage. Always use `TimeSeriesSplit` or a custom temporal splitter that respects `offset_date`.
- **sklearn is CPU-only.** Do not request GPU compute for sklearn training jobs in Azure ML. Use CPU-based compute clusters (e.g., `Standard_DS3_v2`).
- **`n_jobs=-1` on Azure ML compute can cause OOM.** On managed compute, set `n_jobs` to the actual core count or a conservative fraction (e.g., `n_jobs=4` on an 8-core VM).
- **HistGradientBoosting handles categoricals natively** via `categorical_features` parameter — this is the one sklearn exception to the encoding rule.
- **SVM scales poorly beyond ~100K rows.** Use `LinearSVC` for large datasets, or switch to tree-based models.
- **Always set `random_state`** for reproducibility across pipeline runs.

---

## Evaluation criteria checklist

Before handing off a trained sklearn model, verify all of the following:

- [ ] Model was selected based on problem type (classification vs regression) and dataset size
- [ ] Temporal cross-validation was used (NOT random KFold) — `TimeSeriesSplit` or custom temporal splitter
- [ ] Categorical features were encoded before training (unless using HistGradientBoosting with `categorical_features`)
- [ ] Hyperparameter tuning was performed with a reasonable search space
- [ ] Metrics were computed on a held-out temporal validation set (not the CV folds)
- [ ] For regression with log-transformed targets, predictions were inverted before metric computation
- [ ] Model was serialized with `joblib` (not raw pickle)
- [ ] Preprocessing artifacts (scalers, encoders) were saved alongside the model
- [ ] `random_state` was set for reproducibility
- [ ] `n_jobs` was set appropriately for the Azure ML compute size (not blindly `-1`)
- [ ] Metrics were logged to MLflow
- [ ] Model artifacts were logged to MLflow
