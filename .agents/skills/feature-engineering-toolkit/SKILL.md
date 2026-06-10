---
name: feature-engineering-toolkit
description: >
  Use this skill when engineering features for Azure ML pipelines — temporal aggregations, categorical encoding,
  feature interactions, or feature selection. Trigger on: "feature engineering", "create features", "encode categoricals",
  "lag features", "rolling aggregations", "feature selection", "target encoding", or any mention of transforming
  raw data into model-ready features. Do NOT use for data cleaning (use ml-data-cleansing) or EDA (use ml-eda).
compatibility: opencode
metadata:
  stage: feature-engineering
  repos: <your-repo-name>
---

# Feature Engineering Toolkit Skill

## When to load this skill

Load when the task involves: creating new features from raw data, temporal rolling aggregations, lag features, categorical encoding (target encoding, one-hot, frequency), feature interactions, feature selection, or any transformation of raw data into model-ready features for Azure ML pipelines.

---

## Feature engineering workflow

### Step 1 — Understand raw features (use ml-eda first)

Before engineering features, load the **ml-eda** skill and run `profile_dataset` to understand:
- Column types, null rates, cardinality
- Distributions of numeric and categorical columns
- Temporal range and gaps in the data

```python
# Use the profile_dataset tool first
# Then inspect the output for:
# - High-cardinality categoricals (>50 unique values) → frequency or target encoding
# - Low-cardinality categoricals (≤10 unique values) → one-hot encoding
# - Numeric columns with extreme skew → log1p transform
# - Date columns that define temporal boundaries
```

### Step 2 — Temporal feature engineering

All temporal features must respect `offset_date` — this is a **per-row** cutoff, not a global split date.

#### Rolling aggregations
```python
import pandas as pd
import numpy as np

def compute_rolling_features(df: pd.DataFrame, entity_col: str, date_col: str,
                              offset_col: str, value_col: str,
                              windows: list[int] = [30, 90, 180]) -> pd.DataFrame:
    """Compute rolling aggregations respecting per-row offset_date.

    Args:
        df: Source dataframe with entity, date, offset_date, and value columns.
        entity_col: Column name for entity identifier.
        date_col: Column name for the event date.
        offset_col: Column name for the per-row cutoff date.
        value_col: Column name for the numeric value to aggregate.
        windows: List of window sizes in days.

    Returns:
        Dataframe with rolling feature columns per entity.
    """
    results = []
    for _, row in df.groupby(entity_col):
        entity_id = row[entity_col].iloc[0]
        for _, record in row.iterrows():
            offset = record[offset_col]
            history = row[(row[date_col] < offset)]  # STRICT less-than
            feat = {"entity_id": entity_id}
            for w in windows:
                window_start = offset - pd.Timedelta(days=w)
                window_data = history[(history[date_col] >= window_start)][value_col]
                feat[f"{value_col}_rolling_mean_{w}d"] = window_data.mean()
                feat[f"{value_col}_rolling_std_{w}d"] = window_data.std()
                feat[f"{value_col}_rolling_count_{w}d"] = len(window_data)
            results.append(feat)
    return pd.DataFrame(results)
```

#### Lag features
```python
def compute_lag_features(df: pd.DataFrame, entity_col: str, date_col: str,
                          offset_col: str, value_col: str,
                          lags: list[int] = [1, 3, 6]) -> pd.DataFrame:
    """Compute lag features from historical data before offset_date.

    Args:
        df: Source dataframe.
        entity_col: Entity identifier column.
        date_col: Event date column.
        offset_col: Per-row cutoff date column.
        value_col: Numeric value column to lag.
        lags: List of lag periods (in months).

    Returns:
        Dataframe with lag feature columns.
    """
    results = []
    for _, group in df.groupby(entity_col):
        entity_id = group[entity_col].iloc[0]
        sorted_group = group.sort_values(date_col)
        for _, record in group.iterrows():
            offset = record[offset_col]
            history = sorted_group[sorted_group[date_col] < offset]
            feat = {"entity_id": entity_id}
            for lag in lags:
                lag_cutoff = offset - pd.DateOffset(months=lag)
                lag_data = history[history[date_col] >= lag_cutoff][value_col]
                feat[f"{value_col}_lag_{lag}m"] = lag_data.mean()
            results.append(feat)
    return pd.DataFrame(results)
```

#### Expanding window aggregations
```python
def compute_expanding_features(df: pd.DataFrame, entity_col: str, date_col: str,
                                offset_col: str, value_col: str) -> pd.DataFrame:
    """Compute expanding (all-history) aggregations up to offset_date.

    Args:
        df: Source dataframe.
        entity_col: Entity identifier column.
        date_col: Event date column.
        offset_col: Per-row cutoff date column.
        value_col: Numeric value column to aggregate.

    Returns:
        Dataframe with expanding feature columns.
    """
    results = []
    for _, group in df.groupby(entity_col):
        entity_id = group[entity_col].iloc[0]
        for _, record in group.iterrows():
            offset = record[offset_col]
            history = group[(group[entity_col] == entity_id) & (group[date_col] < offset)]
            vals = history[value_col]
            feat = {
                "entity_id": entity_id,
                f"{value_col}_expanding_mean": vals.mean(),
                f"{value_col}_expanding_std": vals.std(),
                f"{value_col}_expanding_count": len(vals),
                f"{value_col}_expanding_max": vals.max(),
                f"{value_col}_expanding_min": vals.min(),
            }
            results.append(feat)
    return pd.DataFrame(results)
```

### Step 3 — Categorical encoding

#### Target encoding (fold-aware, leakage-safe)
```python
from sklearn.model_selection import KFold
import numpy as np

def target_encode_fold_aware(df: pd.DataFrame, col: str, target_col: str,
                               n_folds: int = 5, smoothing: float = 10.0) -> pd.Series:
    """Fold-aware target encoding with smoothing to prevent leakage.

    Computes encoding using only out-of-fold data. Each fold's encoding
    is derived from the global mean and the out-of-fold group mean.

    Args:
        df: Dataframe with the categorical column and target.
        col: Categorical column to encode.
        target_col: Target column name.
        n_folds: Number of folds for cross-validation.
        smoothing: Smoothing parameter (higher = more shrinkage to global mean).

    Returns:
        Series of encoded values aligned to original dataframe index.
    """
    global_mean = df[target_col].mean()
    group_stats = df.groupby(col)[target_col].agg(["mean", "count"]).reset_index()
    group_stats.columns = [col, "group_mean", "group_count"]

    encoded = np.zeros(len(df))
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    for train_idx, val_idx in kf.split(df):
        # Compute stats from training fold only
        train_df = df.iloc[train_idx]
        fold_stats = train_df.groupby(col)[target_col].agg(["mean", "count"]).reset_index()
        fold_stats.columns = [col, "group_mean", "group_count"]

        # Apply smoothing: weighted average of group mean and global mean
        for _, stat in fold_stats.iterrows():
            cat = stat[col]
            n = stat["group_count"]
            smoothed = (n * stat["group_mean"] + smoothing * global_mean) / (n + smoothing)
            mask = df[col].iloc[val_idx] == cat
            encoded[val_idx[mask]] = smoothed

        # Handle unseen categories in validation fold
        unseen_mask = ~df[col].iloc[val_idx].isin(fold_stats[col])
        encoded[val_idx[unseen_mask]] = global_mean

    return pd.Series(encoded, index=df.index)
```

#### One-hot encoding (low cardinality)
```python
def one_hot_encode(df: pd.DataFrame, cols: list[str], max_categories: int = 10) -> pd.DataFrame:
    """One-hot encode low-cardinality categorical columns.

    Args:
        df: Source dataframe.
        cols: List of categorical columns to encode.
        max_categories: Maximum number of unique values to one-hot encode.

    Returns:
        Dataframe with one-hot encoded columns.
    """
    encoded_dfs = [df]
    for col in cols:
        cardinality = df[col].nunique()
        if cardinality <= max_categories:
            dummies = pd.get_dummies(df[col], prefix=col, dtype=int)
            encoded_dfs.append(dummies)
            df = df.drop(columns=[col])
        else:
            logger.warning(f"Column {col} has {cardinality} unique values — "
                          f"skipping one-hot, consider frequency encoding")
    return pd.concat(encoded_dfs, axis=1)
```

#### Frequency encoding (high cardinality)
```python
def frequency_encode(df: pd.DataFrame, col: str) -> pd.Series:
    """Encode a high-cardinality categorical by its frequency.

    Args:
        df: Source dataframe.
        col: Categorical column to encode.

    Returns:
        Series of frequency-encoded values.
    """
    freq = df[col].value_counts(normalize=True)
    return df[col].map(freq)
```

### Step 4 — Feature interactions and polynomial features

Only create interactions for **top-importance** features identified from a preliminary model run.

```python
from sklearn.preprocessing import PolynomialFeatures
import pandas as pd

def create_top_interactions(df: pd.DataFrame, top_features: list[str],
                             degree: int = 2) -> pd.DataFrame:
    """Create polynomial interaction features from top-importance features.

    Args:
        df: Source dataframe.
        top_features: List of top-importance feature columns.
        degree: Polynomial degree (2 = pairwise interactions).

    Returns:
        Dataframe with interaction feature columns.
    """
    poly = PolynomialFeatures(degree=degree, include_bias=False, interaction_only=True)
    X_poly = poly.fit_transform(df[top_features])
    feature_names = poly.get_feature_names_out(top_features)
    # Drop original features (keep only interactions)
    interaction_names = [n for n in feature_names if " " in n]  # interaction terms have spaces
    interaction_cols = X_poly[:, len(top_features):]
    interaction_df = pd.DataFrame(interaction_cols, columns=interaction_names, index=df.index)
    # Replace spaces with underscores for column names
    interaction_df.columns = [c.replace(" ", "_") for c in interaction_df.columns]
    return interaction_df
```

### Step 5 — Feature selection

```python
def select_features_by_importance(feature_importances: dict, top_n: int = 50,
                                   min_importance: float = 0.001) -> list[str]:
    """Select features by importance threshold and top-N cutoff.

    Args:
        feature_importances: Dict mapping feature name to importance score.
        top_n: Maximum number of features to retain.
        min_importance: Minimum importance threshold.

    Returns:
        List of selected feature names.
    """
    sorted_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)
    selected = [name for name, imp in sorted_features
                if imp >= min_importance][:top_n]
    return selected

def drop_high_correlation(df: pd.DataFrame, threshold: float = 0.95) -> list[str]:
    """Identify columns to drop due to high pairwise correlation.

    Args:
        df: Dataframe with numeric features.
        threshold: Correlation threshold above which to drop one of the pair.

    Returns:
        List of column names to drop.
    """
    corr_matrix = df.corr().abs()
    upper = corr_matrix.where(
        np.triu(np.ones(corr_matrix.shape, dtype=bool), k=1)
    )
    to_drop = [col for col in upper.columns if any(upper[col] > threshold)]
    return to_drop
```

---

## Leakage guards

These rules are **non-negotiable** for Azure ML pipelines:

1. **`offset_date` is per-row, not global.** Every temporal aggregation must filter `< offset_date` for that specific row's cutoff. A global `df[df[date_col] < max_offset]` pattern is incorrect and introduces silent leakage.

2. **Target encoding must be fold-aware.** Never compute target encoding on the full dataset. Use KFold to compute out-of-fold encodings. The `target_encode_fold_aware` function above is the reference implementation.

3. **No future information.** Features computed from data on or after `offset_date` are leakage. This includes:
   - Rolling windows that include the offset date itself (use strict `<`)
   - Aggregations that span across the offset boundary
   - Any feature derived from post-offset events

4. **Inference-only features must not appear in training.** Features that are only available after the prediction window (e.g., measurement results computed post-production) must be excluded from the training feature set. They may be used in a separate inference feature set.

5. **New entities at inference have no history.** Rolling features for new entities will be NaN. This is expected — handle with appropriate defaults (e.g., global mean, zero) in the inference pipeline.

---

## Gotchas

- **`offset_date` is per-row, not global.** The most common feature engineering bug. Using a global cutoff date instead of per-row filtering silently leaks future data into features. The model trains well but degrades at inference.

- **New entities at inference have no history.** Rolling aggregations, lag features, and expanding windows all return NaN for entities with no historical data. Plan for this in the inference pipeline with sensible defaults.

- **Feature explosion from interactions.** Polynomial features on 20 top features with degree=2 produces 190 interaction terms. Always follow interactions with feature selection. Do not create interactions on more than 15 features without careful pruning.

- **Target encoding overfitting.** Without fold-aware computation and smoothing, target encoding memorizes the training data. Always use the fold-aware implementation with smoothing ≥ 10.0.

- **Categorical encoding drift.** New category values at inference that were not seen in training will produce NaN in frequency/target encoding. Handle with a fallback to global mean or a dedicated "unknown" category.

- **Rolling window edge cases.** When `offset_date` is very close to the first event date for an entity, rolling windows may contain zero records. Return NaN (not zero) to distinguish "no data" from "data with zero mean".

- **Groupby performance.** Iterating row-by-row for per-row offset filtering is correct but slow. For large datasets, consider sorting by entity and date, then using vectorized cumulative operations with a custom offset-aware window function.

---

## Evaluation criteria

Before handing off feature engineering results, verify all of the following:

- [ ] ml-eda skill was loaded and `profile_dataset` was run to understand raw feature distributions before engineering
- [ ] All temporal features use strict `< offset_date` filtering (per-row, not global)
- [ ] Target encoding uses fold-aware computation with smoothing (no full-dataset encoding)
- [ ] High-cardinality categoricals (>50 unique values) use frequency or target encoding, not one-hot
- [ ] Low-cardinality categoricals (≤10 unique values) use one-hot encoding
- [ ] Feature interactions were created only from top-importance features (not all features)
- [ ] Feature selection was applied after interaction creation to control feature count
- [ ] No inference-only features (unavailable at training time) appear in the training feature set
- [ ] NaN handling for new entities at inference is documented and implemented
- [ ] Feature engineering code is in `engineer_features.py` with proper ArgumentParser and AML component YAML sync

---

## References

See the `references/` directory for detailed reference guides:
- `temporal-features.md` — Rolling windows, lag features, expanding aggregations, offset_date patterns
- `categorical-encoding.md` — Target encoding, one-hot, frequency, ordinal encoding with leakage prevention

See the `scripts/` directory for reusable templates:
- `temporal_aggregations.py` — Template for computing temporal rolling aggregations with offset_date respect
