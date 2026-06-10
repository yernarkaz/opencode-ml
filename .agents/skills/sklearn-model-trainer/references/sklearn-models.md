# Scikit-learn Models Reference

Quick reference for common sklearn models, their key hyperparameters, and when to use each one in Azure ML pipelines.

---

## Classification Models

### LogisticRegression
- **Best for**: Binary/multiclass classification, interpretable baselines, large datasets
- **Key hyperparameters**:
  - `C`: Inverse regularization strength (smaller = stronger regularization). Default: 1.0
  - `penalty`: `"l1"`, `"l2"`, `"elasticnet"`, `None`
  - `solver`: `"lbfgs"`, `"liblinear"`, `"saga"` (l1 requires liblinear or saga)
  - `class_weight`: `"balanced"` for imbalanced data
- **Requires scaling**: Yes (StandardScaler recommended)
- **Handles categoricals**: No — encode first

### RandomForestClassifier
- **Best for**: General-purpose classification, robust to outliers, feature importance extraction
- **Key hyperparameters**:
  - `n_estimators`: Number of trees (100–500 typical)
  - `max_depth`: Tree depth limit (5–20, or `None` for unlimited)
  - `min_samples_split`: Minimum samples to split a node (2–10)
  - `min_samples_leaf`: Minimum samples at leaf (1–4)
  - `max_features`: Features considered per split (`"sqrt"`, `"log2"`, `None`)
  - `class_weight`: `"balanced"` for imbalanced data
- **Requires scaling**: No
- **Handles categoricals**: No — encode first

### GradientBoostingClassifier
- **Best for**: High-accuracy classification, structured/tabular data
- **Key hyperparameters**:
  - `n_estimators`: Number of boosting stages (100–500)
  - `learning_rate`: Shrinkage factor (0.01–0.2, lower = more estimators needed)
  - `max_depth`: Tree depth (3–8)
  - `subsample`: Fraction of samples per tree (0.8–1.0)
  - `min_samples_leaf`: Minimum samples at leaf (5–20)
- **Requires scaling**: No
- **Handles categoricals**: No — encode first

### HistGradientBoostingClassifier
- **Best for**: Large datasets, fast training, native categorical support
- **Key hyperparameters**:
  - `max_iter`: Number of boosting iterations (100–1000)
  - `learning_rate`: Shrinkage factor (0.01–0.2)
  - `max_depth`: Tree depth (3–16, or `None`)
  - `l1_regularization`, `l2_regularization`: Regularization strength
  - `categorical_features`: List of categorical column indices or `"from_dtype"`
- **Requires scaling**: No
- **Handles categoricals**: Yes — via `categorical_features` parameter

### SVC (Support Vector Classifier)
- **Best for**: Small-to-medium datasets, high-dimensional feature spaces
- **Key hyperparameters**:
  - `C`: Regularization parameter (0.1–10.0)
  - `kernel`: `"rbf"`, `"linear"`, `"poly"`, `"sigmoid"`
  - `gamma`: Kernel coefficient (`"scale"`, `"auto"`, or float)
  - `class_weight`: `"balanced"` for imbalanced data
- **Requires scaling**: Yes (critical for SVM)
- **Handles categoricals**: No — encode first
- **Note**: Scales poorly beyond ~100K rows; use `LinearSVC` for large datasets

### KNeighborsClassifier
- **Best for**: Small datasets, simple baselines, non-parametric approach
- **Key hyperparameters**:
  - `n_neighbors`: Number of neighbors (3–20)
  - `weights`: `"uniform"`, `"distance"`
  - `metric`: `"euclidean"`, `"manhattan"`, `"cosine"`
- **Requires scaling**: Yes (distance-based)
- **Handles categoricals**: No — encode first

---

## Regression Models

### LinearRegression
- **Best for**: Baseline regression, interpretable coefficients
- **Key hyperparameters**: None (no regularization)
- **Requires scaling**: No (but affects coefficient interpretation)
- **Handles categoricals**: No — encode first

### Ridge (L2 Regularized Linear Regression)
- **Best for**: Multicollinearity, feature selection via coefficient shrinkage
- **Key hyperparameters**:
  - `alpha`: Regularization strength (0.01–10.0)
- **Requires scaling**: Yes
- **Handles categoricals**: No — encode first

### Lasso (L1 Regularized Linear Regression)
- **Best for**: Feature selection (drives coefficients to zero)
- **Key hyperparameters**:
  - `alpha`: Regularization strength (0.01–10.0)
- **Requires scaling**: Yes
- **Handles categoricals**: No — encode first

### RandomForestRegressor
- **Best for**: General-purpose regression, nonlinear relationships
- **Key hyperparameters**: Same as RandomForestClassifier (see above)
- **Requires scaling**: No
- **Handles categoricals**: No — encode first

### GradientBoostingRegressor
- **Best for**: High-accuracy regression, tabular data
- **Key hyperparameters**: Same as GradientBoostingClassifier (see above)
- **Requires scaling**: No
- **Handles categoricals**: No — encode first

### HistGradientBoostingRegressor
- **Best for**: Large regression datasets, fast training, native categorical support
- **Key hyperparameters**: Same as HistGradientBoostingClassifier (see above)
- **Requires scaling**: No
- **Handles categoricals**: Yes — via `categorical_features` parameter

### SVR (Support Vector Regression)
- **Best for**: Small datasets, robust to outliers
- **Key hyperparameters**:
  - `C`: Regularization parameter
  - `epsilon`: Insensitive loss threshold (0.1–0.5)
  - `kernel`: `"rbf"`, `"linear"`, `"poly"`
- **Requires scaling**: Yes (critical)
- **Handles categoricals**: No — encode first

---

## Model Comparison Summary

| Model | Speed | Accuracy | Interpretability | Scales to large data | Handles categoricals |
|---|---|---|---|---|---|
| LinearRegression | ⚡⚡⚡ | ⭐ | ⭐⭐⭐ | Yes | No |
| Ridge/Lasso | ⚡⚡⚡ | ⭐⭐ | ⭐⭐⭐ | Yes | No |
| LogisticRegression | ⚡⚡⚡ | ⭐⭐ | ⭐⭐⭐ | Yes | No |
| RandomForest | ⚡⚡ | ⭐⭐⭐ | ⭐⭐ | Moderate | No |
| GradientBoosting | ⚡ | ⭐⭐⭐⭐ | ⭐⭐ | Moderate | No |
| HistGradientBoosting | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐ | Yes | Yes |
| SVC/SVR | ⚡ | ⭐⭐⭐ | ⭐ | No | No |
| KNN | ⚡⚡ (train) / ⚡ (predict) | ⭐⭐ | ⭐ | No | No |

---

## Azure ML Pipeline Integration Tips

1. **Use `joblib` for serialization** — it handles numpy arrays in sklearn models more efficiently than pickle
2. **Save preprocessing state** — scalers, encoders, and column transformers must be saved alongside the model
3. **Set `n_jobs` conservatively** — on Azure ML compute, `n_jobs=-1` can cause OOM; use actual core count or a fraction
4. **Log hyperparameters to MLflow** — use `mlflow.log_param()` for each tuned parameter
5. **HistGradientBoosting is the best default** for Azure ML sklearn pipelines — fast, handles categoricals, no scaling needed
