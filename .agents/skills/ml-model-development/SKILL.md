---
name: ml-model-development
description: >
  Use this skill when implementing or modifying training pipelines, model architectures,
  hyperparameter tuning, feature engineering, or overfitting fixes for any ML repo.
  Primary stack is LightGBM, CatBoost, and Optuna — always default to these before any
  alternative. Also use when adding new model types, writing Optuna objective functions,
  or setting up temporal cross-validation. Do NOT use for EDA (use ml-eda), data
  cleaning (use ml-data-cleansing), or evaluation metrics (use ml-evaluation). Trigger
  on: "train a model", "hyperparameter tuning", "overfitting", "feature importance",
  "add CatBoost", "temporal split", "Optuna study", or any task that involves touching
  train_model.py or engineer_features.py.
compatibility: opencode
metadata:
  stage: model-development
  repos: <your-repo-name>
---

# ML Model Development Skill

## When to load this skill
Load when the task involves: implementing or modifying training pipelines, choosing model architectures, hyperparameter tuning, feature selection, addressing overfitting, or adding new model types.

---

## Gotchas

- **`str_to_bool` is required for all boolean CLI flags — never `store_true`/`store_false`.** AML component YAML binds arguments by type. `store_true` produces `bool` from presence/absence of the flag, which the YAML input binding cannot handle. Import `str_to_bool` from `utils/arg_parsing.py`.
- **`PYTHONPATH=aml/pipeline/src` is required for every local script run.** Without it, all internal module imports fail with misleading `ModuleNotFoundError`. The `ml-env.ts` plugin injects this automatically in OpenCode sessions, but CI/CD scripts and direct terminal runs need it set explicitly.
- **`MultiOutputRegressor.feature_importances_` does not exist.** Access per-target importances via `model.estimators_[i].feature_importances_`, where `i` corresponds to the index in `target_cols`.
- **LightGBM early stopping is silently ignored without `eval_set`.** The `lgb.early_stopping(100)` callback does nothing if no evaluation dataset is passed to `model.fit()`. Always verify `eval_set=[(X_val, y_val)]` is present alongside the callback.
- **CatBoost `cat_features` takes names for DataFrames, indices for numpy arrays.** Passing column names when the input has been converted to numpy will raise `CatBoostError`. Pass indices when using numpy: `cat_features=[X_train.columns.get_loc(c) for c in category_cols]`.

---

## Primary stack — use these first

Tree-based models are the default. Use this stack before proposing alternatives.

### LightGBM

```python
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, r2_score

params = {
    "n_estimators": 2000,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "min_child_samples": 20,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
    "objective": "binary",   # or "regression" / "quantile"
    "metric": "auc",         # or "mae"
    "boosting_type": "gbdt",
    "verbose": -1,
    "random_state": 42,
}

model = lgb.LGBMClassifier(**params)  # or LGBMRegressor
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    callbacks=[
        lgb.early_stopping(100),
        lgb.log_evaluation(200),
    ],
)
```

Always cast categorical features before fitting:
```python
X_train[category_features] = X_train[category_features].astype("category")
```

### CatBoost (classification ensemble partner)

```python
from catboost import CatBoostClassifier

model = CatBoostClassifier(
    iterations=1000,
    learning_rate=0.05,
    depth=6,
    l2_leaf_reg=10,
    random_seed=42,
    verbose=200,
    cat_features=category_features,  # pass indices or names
)
model.fit(X_train, y_train, eval_set=(X_val, y_val), early_stopping_rounds=50)
```

### Quantile regression (median prediction for skewed targets)

```python
params = {
    **base_params,
    "objective": "quantile",
    "alpha": 0.5,   # median
    "metric": "mae",
}
```

### Multi-output regression (multiple targets)

```python
from sklearn.multioutput import MultiOutputRegressor

base_model = lgb.LGBMRegressor(**params)
model = MultiOutputRegressor(base_model)
model.fit(X_train, np.log1p(y_train))  # log transform all targets

# Inverse transform and clip
y_pred = np.expm1(model.predict(X_test))
for i, col in enumerate(target_cols):
    y_pred[:, i] = np.where(y_pred[:, i] <= 0, TARGET_CAPS[col][0], y_pred[:, i])
```

---

## Hyperparameter tuning with Optuna

```python
import optuna
from optuna.samplers import TPESampler

def objective(trial: optuna.Trial) -> float:
    params = {
        "learning_rate": trial.suggest_float("learning_rate", 0.001, 0.1, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 10, 200),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 500),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-4, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-4, 10.0, log=True),
    }
    # ... cross-validate and return metric ...
    return mean_cv_score

study = optuna.create_study(direction="maximize", sampler=TPESampler(seed=42))
study.optimize(objective, n_trials=50)
print(f"Best: {study.best_value:.4f} | Params: {study.best_params}")
```

---

## Temporal cross-validation

Always use time-based splits — never random splits for time-series data:

```python
def create_temporal_split(
    df: pd.DataFrame,
    date_col: str,
    train_end_date: pd.Timestamp,
    val_end_date: pd.Timestamp,
) -> dict:
    """Create temporal train/val/test splits."""
    train = df[df[date_col] <= train_end_date]
    val = df[(df[date_col] > train_end_date) & (df[date_col] <= val_end_date)]
    test = df[df[date_col] > val_end_date]
    return {"X_train": train, "X_val": val, "X_test": test}
```

---

## Log transform pattern (skewed regression targets)

```python
# Training
model.fit(X_train, np.log1p(y_train))

# Inference
y_pred_raw = model.predict(X_test)
y_pred = np.expm1(y_pred_raw)
y_pred = np.where(y_pred < 0, MIN_CAP, y_pred)  # clip negatives
```

---

## Overfitting checklist

- [ ] Train/test metric gap > 5%? Increase `min_child_samples`, reduce `num_leaves`
- [ ] Val metric worse than expected? Check temporal leakage
- [ ] High variance across CV folds? Increase `bagging_fraction`, reduce `learning_rate`
- [ ] Too many features? Run RFE or use `feature_importances_` to drop near-zero features
- [ ] Model too complex? Try `n_estimators=500` with early stopping as baseline

---

## Secondary stack — on-demand references

These are not primary pipeline models. Load the reference file only when the user explicitly requires it.

### HuggingFace fine-tuning
Use when: free-text fields (part descriptions, supplier notes) are input features.  
Reference: `references/huggingface.md` in this skill directory.

### PySpark ML
Use when: data exceeds single-machine memory (~50 GB+) or Databricks compute is required.  
Reference: `references/pyspark.md` in this skill directory.

---

## Evaluation criteria

Before handing off a training script or model implementation, verify all of the following:

- [ ] Tree-based primary stack (LightGBM / CatBoost) used by default — HF or PySpark only if explicitly justified
- [ ] Categorical columns cast to `.astype("category")` before `model.fit()`
- [ ] Early stopping configured (`lgb.early_stopping(100)`) — no fixed `n_estimators` without early stopping
- [ ] `random_state=42` / `random_seed=42` set on all models and Optuna study
- [ ] Temporal split used (not random) — `create_temporal_split` or equivalent date-based filter
- [ ] Log transform applied correctly: `log1p` at training, `expm1` at inference (skewed regression targets)
- [ ] Negative predictions clipped after `expm1` inverse transform (regression)
- [ ] `MultiOutputRegressor` wrapping `LGBMRegressor` for multi-target — not separate models per target
- [ ] Optuna study uses `TPESampler(seed=42)` and `direction="maximize"` (classification) or `"minimize"` (regression)
- [ ] Overfitting checklist reviewed — train/test metric gap checked before declaring done
- [ ] No `store_true` / `store_false` in `ArgumentParser` — `str_to_bool` helper used for boolean flags
- [ ] `PYTHONPATH=aml/pipeline/src` set before running any pipeline script
