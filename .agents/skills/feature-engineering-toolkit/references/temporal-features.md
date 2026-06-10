# Temporal Features Reference

## Overview

Temporal features capture historical patterns for each entity up to its `offset_date`. In Azure ML pipelines, every entity has a per-row `offset_date` that defines the cutoff for what information is available. Features must never use data on or after this date.

## Core principle

```
offset_date is per-row, NOT a global split date.
```

Each row may have a different `offset_date`. A global filter like `df[df["date"] < max_offset]` is incorrect — it leaks future data for rows with earlier cutoffs.

---

## Rolling window aggregations

Rolling windows compute statistics over a fixed lookback period (e.g., last 30, 90, 180 days) from each row's `offset_date`.

### Pattern

```python
import pandas as pd
import numpy as np

def rolling_aggregations(events: pd.DataFrame, entity_id: str,
                          offset_date: pd.Timestamp,
                          date_col: str, value_col: str,
                          windows: list[int]) -> dict:
    """Compute rolling aggregations for a single entity up to its offset_date.

    Args:
        events: All historical events for this entity.
        entity_id: Entity identifier.
        offset_date: Per-row cutoff date (exclusive).
        date_col: Name of the date column in events.
        value_col: Name of the numeric value column.
        windows: List of window sizes in days.

    Returns:
        Dict of feature name → value.
    """
    # Filter to events strictly before offset_date
    history = events[events[date_col] < offset_date]

    features = {}
    for w in windows:
        window_start = offset_date - pd.Timedelta(days=w)
        window_data = history[(history[date_col] >= window_start)][value_col]

        features[f"{value_col}_mean_{w}d"] = window_data.mean()
        features[f"{value_col}_std_{w}d"] = window_data.std()
        features[f"{value_col}_count_{w}d"] = len(window_data)
        features[f"{value_col}_sum_{w}d"] = window_data.sum()
        features[f"{value_col}_max_{w}d"] = window_data.max()
        features[f"{value_col}_min_{w}d"] = window_data.min()

    return features
```

### Common window sizes

| Use case | Windows |
|---|---|
| Short-term trends | 7d, 14d, 30d |
| Medium-term trends | 30d, 90d, 180d |
| Long-term trends | 90d, 180d, 365d |
| Manufacturing quality | 30d, 90d, 180d, 365d |

### Edge cases

- **No history before offset_date**: All features return NaN. This is expected for new entities. Do not fill with zero — use NaN to distinguish "no data" from "data with zero mean".
- **Window larger than available history**: The window naturally shrinks to available data. This is correct behavior.
- **Single event in window**: `std()` returns NaN. Handle gracefully.

---

## Lag features

Lag features capture the value (or aggregation) from a specific period ago relative to `offset_date`.

### Pattern

```python
def lag_features(events: pd.DataFrame, offset_date: pd.Timestamp,
                  date_col: str, value_col: str,
                  lags: list[int]) -> dict:
    """Compute lag features for a single entity.

    Args:
        events: All historical events for this entity.
        offset_date: Per-row cutoff date (exclusive).
        date_col: Name of the date column.
        value_col: Name of the numeric value column.
        lags: List of lag periods in months.

    Returns:
        Dict of feature name → value.
    """
    history = events[events[date_col] < offset_date]

    features = {}
    for lag in lags:
        lag_cutoff = offset_date - pd.DateOffset(months=lag)
        lag_data = history[history[date_col] >= lag_cutoff][value_col]
        features[f"{value_col}_lag_{lag}m"] = lag_data.mean()

    return features
```

### When to use lags vs rolling

- **Lags**: When you want to compare specific periods (e.g., "last quarter vs. current quarter")
- **Rolling**: When you want continuous trend signals (e.g., "average over last 90 days")

---

## Expanding window aggregations

Expanding windows use all available history up to `offset_date`. These capture the entity's complete historical profile.

### Pattern

```python
def expanding_features(events: pd.DataFrame, offset_date: pd.Timestamp,
                        date_col: str, value_col: str) -> dict:
    """Compute expanding (all-history) aggregations.

    Args:
        events: All historical events for this entity.
        offset_date: Per-row cutoff date (exclusive).
        date_col: Name of the date column.
        value_col: Name of the numeric value column.

    Returns:
        Dict of feature name → value.
    """
    history = events[events[date_col] < offset_date]
    vals = history[value_col]

    return {
        f"{value_col}_all_mean": vals.mean(),
        f"{value_col}_all_std": vals.std(),
        f"{value_col}_all_count": len(vals),
        f"{value_col}_all_max": vals.max(),
        f"{value_col}_all_min": vals.min(),
        f"{value_col}_all_median": vals.median(),
    }
```

---

## Rate of change features

Rate of change features compare two periods to capture trends.

### Pattern

```python
def rate_of_change(events: pd.DataFrame, offset_date: pd.Timestamp,
                    date_col: str, value_col: str,
                    window_a: int, window_b: int) -> dict:
    """Compute rate of change between two rolling windows.

    Args:
        events: All historical events for this entity.
        offset_date: Per-row cutoff date (exclusive).
        date_col: Name of the date column.
        value_col: Name of the numeric value column.
        window_a: Earlier window size in days.
        window_b: Later window size in days.

    Returns:
        Dict with rate of change feature.
    """
    history = events[events[date_col] < offset_date]

    # Earlier window
    start_a = offset_date - pd.Timedelta(days=window_a + window_b)
    end_a = offset_date - pd.Timedelta(days=window_b)
    window_a_data = history[(history[date_col] >= start_a) & (history[date_col] < end_a)][value_col]

    # Later window
    start_b = offset_date - pd.Timedelta(days=window_b)
    window_b_data = history[(history[date_col] >= start_b)][value_col]

    mean_a = window_a_data.mean() if len(window_a_data) > 0 else np.nan
    mean_b = window_b_data.mean() if len(window_b_data) > 0 else np.nan

    if not np.isnan(mean_a) and mean_a != 0:
        roc = (mean_b - mean_a) / abs(mean_a)
    else:
        roc = np.nan

    return {f"{value_col}_roc_{window_b}d_vs_{window_a}d": roc}
```

---

## Offset_date patterns

### Correct: Per-row filtering

```python
# CORRECT — each row uses its own offset_date
for _, row in df.iterrows():
    offset = row["offset_date"]
    history = events[events["date"] < offset]  # Per-row cutoff
```

### Incorrect: Global filtering

```python
# WRONG — leaks future data for rows with earlier offsets
global_cutoff = df["offset_date"].max()
history = events[events["date"] < global_cutoff]  # Global cutoff
```

### Vectorized approach (for performance)

For large datasets, row-by-row iteration is slow. Use a merge-based approach:

```python
def vectorized_rolling(df: pd.DataFrame, events: pd.DataFrame,
                        entity_col: str, date_col: str,
                        offset_col: str, value_col: str,
                        window_days: int) -> pd.Series:
    """Vectorized rolling aggregation using merge_asof.

    Args:
        df: Main dataframe with offset_date per row.
        events: Event-level data to aggregate.
        entity_col: Entity identifier column.
        date_col: Date column in events.
        offset_col: Offset date column in df.
        value_col: Value column to aggregate.
        window_days: Rolling window size in days.

    Returns:
        Series of rolling mean values aligned to df index.
    """
    # Merge events with df on entity, then filter by date
    merged = df[[entity_col, offset_col]].merge(events, on=entity_col, how="left")
    merged = merged[merged[date_col] < merged[offset_col]]  # Per-row filter
    merged = merged[merged[date_col] >= merged[offset_col] - pd.Timedelta(days=window_days)]

    # Aggregate
    result = merged.groupby(offset_col)[value_col].mean()
    return result
```

---

## Performance considerations

| Approach | Pros | Cons |
|---|---|---|
| Row-by-row iteration | Correct, easy to understand | Slow for large datasets |
| Merge-based vectorized | Fast, scales well | More complex logic |
| Groupby + apply | Moderate speed | Memory intensive for large groups |
| Pre-computed event tables | Fastest at inference | Requires materialized feature store |

For Azure ML pipeline scripts, the row-by-row approach is acceptable for datasets under ~100K entities. For larger datasets, use the vectorized merge approach or pre-compute features in a separate pipeline step.
