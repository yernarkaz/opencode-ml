---
name: ml-data-cleansing
description: >
  Use this skill when cleaning or preparing raw data for any ML
  pipeline — null handling, outlier capping, deduplication, date parsing, categorical
  encoding, or adding post-cleaning validation assertions. Also use when modifying
  preprocess_clean_data.py or any AML pipeline component that touches raw data.
  Do NOT use for EDA or profiling (use ml-eda) or for feature creation (use
  ml-model-development). Trigger on: "clean the data", "handle nulls", "there are
  duplicates", "encode categoricals", "outliers in the target", "prep data for
  training", or any mention of preprocess_clean_data.py.
compatibility: opencode
metadata:
  stage: data-cleansing
  repos: <your-repo-name>
---

# ML Data Cleansing Skill

## When to load this skill
Load when the task involves: cleaning raw data, handling nulls, encoding categoricals, normalising column formats, deduplication, handling outliers, preparing data for feature engineering.

---

## Data cleansing principles

1. **Never drop rows silently** — log every removal with reason and count
2. **Preserve raw data** — always write cleaned output to a new file/path, never overwrite source
3. **Document decisions** — every imputation or exclusion rule must be traceable to a business reason
4. **Validate output** — assert expected row counts and null rates after every transformation

---

## Standard cleansing pipeline pattern (AML component)

```python
def clean_data(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Clean raw data for ML pipeline.

    Args:
        df: Raw input DataFrame.
        config: Cleaning configuration dict.

    Returns:
        Cleaned DataFrame.
    """
    original_rows = len(df)
    logger.info(f"Input rows: {original_rows:,}")

    # 1. Deduplication
    df = df.drop_duplicates()
    logger.info(f"After dedup: {len(df):,} rows (removed {original_rows - len(df):,})")

    # 2. Date parsing
    df[config["date_column"]] = pd.to_datetime(df[config["date_column"]], errors="coerce")
    nat_count = df[config["date_column"]].isna().sum()
    if nat_count > 0:
        logger.warning(f"Dropped {nat_count} rows with unparseable dates")
    df = df.dropna(subset=[config["date_column"]])

    # 3. Target null removal
    target_null_count = df[config["target_column"]].isna().sum()
    if target_null_count > 0:
        logger.warning(f"Dropped {target_null_count} rows with null target")
    df = df.dropna(subset=[config["target_column"]])
    logger.info(f"After target null removal: {len(df):,} rows")

    # 4. Column normalisation
    df = _normalise_columns(df)

    logger.info(f"Final rows: {len(df):,} ({len(df)/original_rows*100:.1f}% retained)")
    return df
```

---

## Gotchas

- **`pd.to_datetime(..., errors="coerce")` is silent.** It does not raise or warn on unparseable values — it converts them to `NaT`. You must check `df[col].isna().sum()` explicitly after parsing to know how many rows were affected.
- **`.astype("category")` must be applied consistently to train and inference.** LightGBM encodes category levels from the training set. If inference data has different or new levels, predictions are silently wrong. Always align categories: `X_infer[col] = X_infer[col].astype(X_train[col].dtype)`.
- **`drop_duplicates()` on all columns is almost always wrong.** The effective dedup key is your natural composite key (e.g. entity ID + date + context), not every column. Deduplication on all columns will miss logical duplicates with minor column differences. Define the key explicitly via `drop_duplicates(subset=[...])`.
- **Never `fillna(0)` for ID columns.** A null ID means the row cannot be joined to any reference data — the row must be dropped, not filled. A zero-filled ID will silently join to unrelated records.
- **Outlier capping bounds must be computed on training data only, then applied to val/test.** Computing bounds on the full dataset leaks test distribution into the transform. Fit `.quantile(0.01)` / `.quantile(0.99)` on `X_train`, then apply to all splits.

---

## Null handling strategies by column type

| Column type | Strategy | Rationale |
|---|---|---|
| Target column | Drop row | Cannot impute ground truth |
| Date column | Drop row after logging | Invalid temporal index |
| Numeric feature — low null (<5%) | Median imputation | Robust to outliers |
| Numeric feature — high null (>20%) | Flag column + drop or keep with indicator | High null = likely structural |
| Categorical feature | Mode or `"UNKNOWN"` category | Preserves row, signals missingness |
| ID columns (entity keys) | Drop row if null | Cannot join without key |

---

## Outlier handling

For regression targets (e.g. continuous positive-valued targets):
```python
# Use percentile-based capping, not removal — removal loses signal
Q1 = df[col].quantile(0.01)
Q99 = df[col].quantile(0.99)
df[col] = df[col].clip(lower=Q1, upper=Q99)
logger.info(f"Clipped {col} to [{Q1:.2f}, {Q99:.2f}]")
```

For classification features, cap at the 99th percentile only when the feature has extreme skew (skew > 5).

---

## Categorical encoding decisions

| Cardinality | Encoding | Example |
|---|---|---|
| Binary | 0/1 integer | `is_active` |
| Low (2–15) | pd.Categorical (for LightGBM native handling) | `status`, `rating` |
| Medium (15–100) | Target encoding with CV folds | `category_code`, `entity_group` |
| High (>100) | Frequency encoding or drop | `entity_id` as raw feature |

For LightGBM: always cast categorical columns with `.astype("category")` before fitting:
```python
X_train[category_features] = X_train[category_features].astype("category")
```

---

## Validation assertions after cleaning

```python
# Add to end of every cleaning function
assert df[target_column].notna().all(), "Target has nulls after cleaning"
assert df[date_column].notna().all(), "Date column has nulls after cleaning"
assert len(df) > 0, "Empty DataFrame after cleaning"
assert df.duplicated().sum() == 0, "Duplicates remain after dedup"
logger.info("All cleaning assertions passed")
```

---

## Evaluation criteria

Before handing off cleaned data or cleaning code, verify all of the following:

- [ ] Raw source data was never overwritten — cleaned output written to a new path
- [ ] Every row removal is logged with reason and count via `logger.warning` (not silent)
- [ ] Target column has zero nulls after cleaning (`assert df[target_column].notna().all()`)
- [ ] Date column has zero nulls after cleaning (`pd.to_datetime(..., errors="coerce")` used, NaTs logged and dropped)
- [ ] ID columns (entity keys) have no nulls — rows dropped if null
- [ ] Deduplication performed and count logged
- [ ] Numeric feature null strategy matches the null rate threshold table (median <5%, indicator >20%)
- [ ] Outlier capping applied to regression targets using percentile bounds (not removal)
- [ ] Categorical columns with LightGBM usage cast to `.astype("category")` after encoding
- [ ] All four validation assertions present at end of cleaning function
- [ ] `logger` used (not `print`) — module-level `logging.getLogger(__name__)` defined
- [ ] Final retained row count and percentage logged at `INFO` level
