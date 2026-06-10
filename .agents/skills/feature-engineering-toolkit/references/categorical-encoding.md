# Categorical Encoding Reference

## Overview

Categorical encoding transforms categorical columns into numeric representations suitable for tree-based models (LightGBM, CatBoost) and linear models. The choice of encoding strategy depends on cardinality, model type, and leakage risk.

## Decision framework

```
Cardinality ≤ 10  →  One-hot encoding
Cardinality 11-50 →  Target encoding (fold-aware) or frequency encoding
Cardinality > 50  →  Frequency encoding or target encoding (fold-aware)
Ordinal categories →  Ordinal encoding (only if natural ordering exists)
```

---

## One-hot encoding

### When to use

- Low cardinality (≤10 unique values)
- No inherent ordering
- Linear models (tree models handle categoricals natively)

### Implementation

```python
import pandas as pd

def one_hot_encode(df: pd.DataFrame, cols: list[str],
                    max_categories: int = 10) -> pd.DataFrame:
    """One-hot encode low-cardinality categorical columns.

    Args:
        df: Source dataframe.
        cols: List of categorical columns to encode.
        max_categories: Maximum cardinality to one-hot encode.

    Returns:
        Dataframe with one-hot encoded columns.
    """
    result = df.copy()
    for col in cols:
        cardinality = result[col].nunique()
        if cardinality <= max_categories:
            dummies = pd.get_dummies(result[col], prefix=col, dtype=int)
            result = pd.concat([result.drop(columns=[col]), dummies], axis=1)
        else:
            logger.warning(f"Column {col} has {cardinality} unique values — "
                          f"skipping one-hot encoding")
    return result
```

### Leakage considerations

One-hot encoding is inherently leakage-safe — it uses only the categorical value itself, not any relationship to the target.

### Inference handling

New category values at inference produce no columns. Handle by:
1. Ensuring all possible categories are defined in the encoding schema during training
2. Using `pd.get_dummies(..., dummy_na=True)` to handle NaN categories
3. Reconciling columns in the inference script to match training schema

---

## Target encoding

### When to use

- Medium to high cardinality
- Tree-based models (LightGBM, CatBoost)
- When the categorical has predictive signal in the target

### Leakage risk

**Target encoding is the highest-leakage-risk encoding method.** Computing the encoding on the full dataset memorizes the target distribution per category. The model then trivially predicts from the encoded values.

### Fold-aware implementation (leakage-safe)

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

def target_encode_fold_aware(df: pd.DataFrame, col: str, target_col: str,
                               n_folds: int = 5, smoothing: float = 10.0) -> pd.Series:
    """Fold-aware target encoding with smoothing to prevent leakage.

    Each fold's encoding is computed from the other folds only.
    Smoothing shrinks category means toward the global mean.

    Args:
        df: Dataframe with the categorical column and target.
        col: Categorical column to encode.
        target_col: Target column name.
        n_folds: Number of cross-validation folds.
        smoothing: Smoothing parameter (higher = more shrinkage to global mean).

    Returns:
        Series of encoded values aligned to original dataframe index.
    """
    global_mean = df[target_col].mean()
    encoded = np.full(len(df), global_mean)

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

    for train_idx, val_idx in kf.split(df):
        # Compute stats from training fold only
        train_df = df.iloc[train_idx]
        fold_stats = train_df.groupby(col)[target_col].agg(["mean", "count"]).reset_index()
        fold_stats.columns = [col, "group_mean", "group_count"]

        # Build lookup
        lookup = fold_stats.set_index(col)[["group_mean", "group_count"]].to_dict("index")

        # Encode validation fold
        for idx in val_idx:
            cat = df[col].iloc[idx]
            if cat in lookup:
                stat = lookup[cat]
                n = stat["group_count"]
                smoothed = (n * stat["group_mean"] + smoothing * global_mean) / (n + smoothing)
                encoded[idx] = smoothed
            # else: stays at global_mean

    return pd.Series(encoded, index=df.index)
```

### Smoothing parameter guidance

| Smoothing | Behavior |
|---|---|
| 1.0 | Minimal shrinkage — risky for small categories |
| 10.0 | Balanced — recommended default |
| 50.0 | Strong shrinkage — safe but loses signal |
| 100.0 | Near-global-mean — conservative |

### Inference handling

At inference, use the full training dataset to compute the encoding (no fold split needed since there's no target to leak from). Apply the same smoothing formula.

```python
def target_encode_inference(train_df: pd.DataFrame, inference_df: pd.DataFrame,
                              col: str, target_col: str,
                              smoothing: float = 10.0) -> pd.Series:
    """Compute target encoding for inference using full training data.

    Args:
        train_df: Training dataframe (used to build encoding).
        inference_df: Inference dataframe to encode.
        col: Categorical column to encode.
        target_col: Target column in training data.
        smoothing: Smoothing parameter.

    Returns:
        Series of encoded values for inference dataframe.
    """
    global_mean = train_df[target_col].mean()
    train_stats = train_df.groupby(col)[target_col].agg(["mean", "count"]).reset_index()
    train_stats.columns = [col, "group_mean", "group_count"]

    lookup = train_stats.set_index(col)[["group_mean", "group_count"]].to_dict("index")

    encoded = []
    for cat in inference_df[col]:
        if cat in lookup:
            stat = lookup[cat]
            n = stat["group_count"]
            smoothed = (n * stat["group_mean"] + smoothing * global_mean) / (n + smoothing)
            encoded.append(smoothed)
        else:
            encoded.append(global_mean)

    return pd.Series(encoded, index=inference_df.index)
```

---

## Frequency encoding

### When to use

- High cardinality (>50 unique values)
- When target encoding is too risky (small dataset, high overfitting risk)
- When the frequency of a category is itself predictive

### Implementation

```python
import pandas as pd

def frequency_encode(df: pd.DataFrame, col: str) -> pd.Series:
    """Encode a categorical column by its relative frequency.

    Args:
        df: Source dataframe.
        col: Categorical column to encode.

    Returns:
        Series of frequency-encoded values (0.0 to 1.0).
    """
    freq = df[col].value_counts(normalize=True)
    return df[col].map(freq).fillna(0.0)
```

### Leakage considerations

Frequency encoding is leakage-safe — it uses only the distribution of the categorical column, not the target. However, the frequency distribution at inference may differ from training (concept drift).

### Inference handling

Compute frequency from training data, apply to inference data. Unseen categories map to 0.0 (or a small epsilon like 1e-6).

---

## Ordinal encoding

### When to use

- Categories have a natural ordering (e.g., severity levels, education levels)
- The ordering is semantically meaningful and consistent

### Implementation

```python
import pandas as pd

def ordinal_encode(df: pd.DataFrame, col: str,
                    order: list[str]) -> pd.Series:
    """Encode an ordinal categorical column using a predefined order.

    Args:
        df: Source dataframe.
        col: Categorical column to encode.
        order: List of category values in ascending order.

    Returns:
        Series of integer-encoded values.
    """
    mapping = {val: idx for idx, val in enumerate(order)}
    return df[col].map(mapping).fillna(-1).astype(int)
```

### Leakage considerations

Ordinal encoding is leakage-safe — it uses only the predefined ordering, not any data-derived statistics.

### Gotcha

Do not use ordinal encoding for nominal categories (no natural order). The model may incorrectly learn ordinal relationships that do not exist.

---

## Encoding comparison

| Method | Leakage risk | Best for | Inference complexity |
|---|---|---|---|
| One-hot | None | Low cardinality, linear models | Must reconcile columns |
| Target (fold-aware) | Low (if fold-aware) | Medium-high cardinality, tree models | Must store training stats |
| Frequency | None | High cardinality, any model | Must store training frequencies |
| Ordinal | None | Ordered categories, any model | Must store ordering |

---

## Best practices

1. **Always use fold-aware target encoding.** Never compute target encoding on the full dataset during training.
2. **Store encoding artifacts.** Save the encoding schema (frequencies, target means, orderings) alongside the model for consistent inference.
3. **Handle unseen categories.** At inference, categories not seen in training must map to a safe default (global mean for target encoding, 0.0 for frequency, -1 for ordinal).
4. **Document encoding decisions.** Record which columns use which encoding method and why, in the feature engineering documentation.
5. **Reconcile at inference.** Ensure the inference pipeline produces the same encoded columns as training, in the same order.
