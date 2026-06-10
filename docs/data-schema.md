# Data Schema — `<FILL IN: repository name>`

> **Template** — Replace every `<FILL IN>` placeholder with values specific to your use-case.
> Delete guidance text in square brackets `[...]` once filled.

---

## Repository

| Property | Value |
|----------|-------|
| Name | `<FILL IN: short repo name, e.g. churn-prediction>` |
| Problem type | `<FILL IN: binary classification / multi-class classification / regression>` |
| Primary metric | `<FILL IN: e.g. roc_auc, f2_score, r_squared, mape>` |

---

## Raw Data Sources

| Source | Format | Path pattern | Refresh frequency |
|--------|--------|--------------|-------------------|
| `<FILL IN: e.g. customer_transactions>` | `<FILL IN: parquet / CSV / Delta>` | `<FILL IN: e.g. abfss://raw/@{dataset}/transactions/*.parquet>` | `<FILL IN: daily / weekly / monthly>` |
| `<FILL IN: e.g. customer_profiles>` | `<FILL IN>` | `<FILL IN>` | `<FILL IN>` |
| `<FILL IN: add more rows as needed>` | | | |

---

## Feature Columns

| Column | Dtype | Description | Source table | Encoding |
|--------|-------|-------------|--------------|----------|
| `<FILL IN: e.g. account_age_days>` | `<FILL IN: int64 / float64 / category>` | `<FILL IN: brief description>` | `<FILL IN: source table>` | `<FILL IN: none / one-hot / target / ordinal>` |
| `<FILL IN>` | `<FILL IN>` | `<FILL IN>` | `<FILL IN>` | `<FILL IN>` |
| `<FILL IN: add more rows as needed>` | | | | |

---

## Target Column(s)

| Column | Dtype | Definition | Transformation |
|--------|-------|------------|----------------|
| `<FILL IN: e.g. churn_flag>` | `<FILL IN: bool / int64 / float64>` | `<FILL IN: e.g. 1 if customer cancelled within 30 days of offset_date>` | `<FILL IN: none / log1p for skewed regression targets>` |
| `<FILL IN: multi-target models add rows here>` | | | |

---

## Temporal Columns

| Property | Value |
|----------|-------|
| **Offset date column** | `<FILL IN: e.g. offset_date — per-row date that defines the "as-of" snapshot for features>` |
| **Temporal split strategy** | `<FILL IN: e.g. 70/15/15 chronological split by offset_date; no shuffling>` |
| **Lookback window** | `<FILL IN: e.g. 365 days of history aggregated per row; features computed over (offset_date - 365d, offset_date]>` |
| **Gap handling** | `<FILL IN: e.g. rows with >90-day gaps in source data are excluded / forward-filled>` |

---

## Entity Identifiers

| Identifier | Description |
|------------|-------------|
| `<FILL IN: e.g. customer_id>` | `<FILL IN: primary entity key; used for groupby aggregations and leakage checks>` |
| `<FILL IN: e.g. account_id>` | `<FILL IN: secondary grouping key, if applicable>` |

---

## Known Data Quality Issues

| Issue | Impact | Mitigation |
|-------|--------|------------|
| `<FILL IN: e.g. entity_id instability — customer_id changes after account merge>` | `<FILL IN: e.g. can cause duplicate entities in aggregations>` | `<FILL IN: e.g. deduplicate on (customer_id, offset_date) keeping latest record>` |
| `<FILL IN: e.g. date gaps in transaction feed during holiday weeks>` | `<FILL IN>` | `<FILL IN>` |
| `<FILL IN: add more rows as needed>` | | |
