---
name: ml-eda
description: >
  Use this skill when exploring or profiling data for any ML repo before modelling —
  shape checks, null rates, target distribution, leakage audits, feature correlation,
  or temporal gap analysis. Also use when diagnosing mid-pipeline data quality issues
  or verifying offset_date boundaries are respected. Do NOT use for cleaning or
  transforming data (use ml-data-cleansing) or for feature engineering decisions
  (use ml-model-development). Trigger even if the user does not say "EDA" — any
  mention of "look at the data", "check the distribution", "is there leakage",
  "profile this dataset", or "something looks off with the features" qualifies.
compatibility: opencode
metadata:
  stage: eda
  repos: <your-repo-name>
---

# ML EDA Skill

## When to load this skill
Load when the task involves: exploratory data analysis, data profiling, understanding a new dataset, distribution analysis, feature correlation, identifying data issues before modelling.

---

## EDA workflow

### Step 1 — Profile first, explore second
Always run `profile_dataset` tool before writing any analysis code. It surfaces shape, nulls, cardinality, and skew in seconds. Only write custom code for patterns the tool does not cover.

### Step 2 — Temporal structure check
For time-series datasets, always establish:
```python
print(df[date_column].min(), df[date_column].max())
print(df[date_column].nunique(), "unique dates")
print(df.groupby(date_column).size().describe())
```
Check for date gaps — missing months signal upstream ADF pipeline failures.

### Step 3 — Target analysis

**Binary classification**
```python
print(df[target_col].value_counts(normalize=True))
# Confirm positive rate matches your use-case baseline — flag if outside expected range
```

**Regression with log transform**
```python
import numpy as np
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
df[target_col].hist(bins=50, ax=axes[0], title="Raw")
np.log1p(df[target_col]).hist(bins=50, ax=axes[1], title="log1p")
plt.tight_layout()
```
If the log-transformed distribution is approximately normal, log transform is appropriate.

### Step 4 — Leakage audit
For temporal datasets, every feature must be computable from data available **before** `offset_date`:
```python
# Red flag: any column that looks like it encodes outcome information
suspicious = [c for c in df.columns if any(
    kw in c.lower() for kw in ["incident", "complaint", "nok", "reject", "fail"]
) and c != target_col]
print("Potential leakage columns:", suspicious)
```

### Step 5 — Correlation and feature importance (quick pass)
```python
from sklearn.ensemble import RandomForestClassifier  # or Regressor
import pandas as pd

# Quick importances without hypertuning
model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X_sample, y_sample)
importances = pd.Series(model.feature_importances_, index=X_sample.columns)
print(importances.sort_values(ascending=False).head(20))
```

---

## Gotchas

- **`offset_date` is per-row, not global.** Every feature aggregation must filter `< offset_date` on that specific row, not on a global max date. Getting this wrong introduces target leakage silently — the model will look good in training but degrade at inference.
- **Inference-only features must not appear in training data.** Some features are unavailable for new records at training time (e.g. measurement aggregations computed after part production). Using them in training produces inflated metrics that will not hold at inference.
- **Missing join data for new records is expected at inference.** New entities have no historical data — joins return NULLs. This is not a pipeline error; it is why a separate inference feature set may be needed.
- **Entity identifiers may not be stable over time.** The same physical entity may receive a new ID following system migrations. Longitudinal analysis must account for this.
- **Date gaps signal upstream pipeline failures, not sparse data.** If a month is entirely missing from the temporal range, the most likely cause is an upstream pipeline outage — flag it for engineering, do not impute.

---

## Common data quality patterns

| Issue | Signal | Action |
|---|---|---|
| Entity ID changes over time | Same physical entity gets new ID after system migration | Flag for business confirmation |
| Key column format inconsistency | Mixed formats in ID or grouping columns | Normalise to consistent format |
| Missing join data for new records | Join returns nulls for recently created entities | Expected at inference — use inference-only feature set if applicable |
| New category values not in training | New category codes not seen at training time | Update encoding and retrain |
| Date column as string | `pd.to_datetime()` fails silently on mixed formats | Always parse with `errors="coerce"` and check NaTs |

---

## EDA notebook structure (follow existing convention)
```
00_data_acquisition.ipynb   — load raw data, verify row counts
01_exploratory_data_analysis.ipynb — distributions, correlations
02_feature_engineering.ipynb — derived features, encoding decisions
```
Save plots to `eda-plots/` directory. Save markdown summaries as `EDA-insights.md`.

---

## Evaluation criteria

Before handing off EDA results, verify all of the following:

- [ ] `profile_dataset` tool was run and output reviewed before any custom analysis code was written
- [ ] Temporal range and date gaps have been confirmed; missing months flagged if present
- [ ] Target distribution is within expected range for your use-case (confirm positive rate for classification; confirm log-transform is appropriate for regression)
- [ ] Leakage audit completed — no columns that could encode future outcome information present as features
- [ ] `offset_date` boundary respected — no features computed from data on or after `offset_date`
- [ ] Quick feature importance pass completed (RandomForest or similar); top-20 features listed
- [ ] Common data quality patterns checked (entity ID stability, key column format inconsistency, NaT dates, new category codes)
- [ ] Plots saved to `eda-plots/` and markdown summary written as `EDA-insights.md`
- [ ] No hardcoded absolute file paths in analysis code — paths taken from args or config
