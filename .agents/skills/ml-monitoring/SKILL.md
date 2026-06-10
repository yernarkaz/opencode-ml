---
name: ml-monitoring
description: >
  Use this skill when monitoring deployed ML endpoints, checking for data drift or model
  performance degradation, or configuring Azure ML monitoring schedules. Trigger on:
  "monitor endpoint", "data drift", "model drift", "endpoint health", "monitoring
  schedule", "drift detection", "production monitoring", or any mention of checking
  a deployed model's behaviour in production.
compatibility: opencode
metadata:
  stage: monitoring
  repos: <your-repo-name>
---

# ML Monitoring Skill

## When to load this skill
Load when the task involves: monitoring deployed ML endpoints, checking for data drift or model performance degradation, configuring Azure ML monitoring schedules, investigating endpoint health issues, or reviewing production data quality.

---

## Gotchas

- **Monitoring baseline must be production data, not training data.** A drift signal computed against training data will always fire because production data is inherently different (new entities, different time period, different feature distributions). Use a representative sample of early production data as the baseline.
- **Seasonal patterns cause false-positive drift alerts.** If your data has weekly or monthly seasonality, a monthly monitoring run comparing against a baseline from a different season will trigger drift. Use rolling baselines or seasonally-adjusted baselines.
- **New entities have no historical features.** At inference time, new entities produce all-null historical aggregations. This is expected and will register as drift if the baseline does not account for the same proportion of new entities.
- **Azure ML monitoring schedules run on a fixed cadence — they do not react to events.** A daily schedule will not catch a drift that happens mid-day. For critical endpoints, combine scheduled monitoring with real-time alerting on latency and error rates.
- **`az ml schedule` commands require the workspace to have the Data Labeling and Monitoring feature enabled.** If the feature is not enabled, schedule creation will fail silently or return a confusing error. Check with `az ml workspace show --query properties` first.

---

## Monitoring workflow

### Step 1 — Check endpoint health

Verify the endpoint is accepting traffic and the deployment is healthy:

```bash
# Endpoint status and traffic routing
az ml online-endpoint show \
  --name <endpoint> \
  --workspace-name <ws> \
  --resource-group <rg> \
  --query "{state:properties.provisioningState, traffic:properties.traffic, authMode:properties.authMode}"

# Deployment health and resource utilisation
az ml online-deployment show \
  --name <deployment> \
  --endpoint-name <endpoint> \
  --workspace-name <ws> \
  --resource-group <rg> \
  --query "{state:properties.provisioningState, instanceCount:properties.instanceCount, requestCount:properties.requestCount, requestSucceededCount:properties.requestSucceededCount, requestFailedCount:properties.requestFailedCount}"

# Recent deployment logs (last 200 lines)
az ml online-deployment get-logs \
  --name <deployment> \
  --endpoint-name <endpoint> \
  --workspace-name <ws> \
  --resource-group <rg> \
  --lines 200
```

Health indicators:
- `provisioningState` is `Succeeded` on both endpoint and deployment
- `requestFailedCount` is 0 or near 0 relative to `requestSucceededCount`
- No `OutOfMemoryError` or `ConnectionRefused` lines in deployment logs
- Response latency under 2s for single-row payloads

### Step 2 — Check data drift

Compare current production feature distributions against the baseline:

```python
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, chi2

def jensen_shannon_distance(p: np.ndarray, q: np.ndarray) -> float:
    """Compute Jensen-Shannon divergence between two distributions.

    Args:
        p: Probability distribution 1 (baseline).
        q: Probability distribution 2 (current).

    Returns:
        Jensen-Shannon distance (0 = identical, 1 = maximally different).
    """
    m = 0.5 * (p + q)
    # Clip to avoid log(0)
    p_clip = np.clip(p, 1e-10, None)
    q_clip = np.clip(q, 1e-10, None)
    m_clip = np.clip(m, 1e-10, None)
    return float(0.5 * np.sum(p_clip * np.log2(p_clip / m_clip)) +
                 0.5 * q_clip * np.log2(q_clip / m_clip))


def compute_psi(baseline: np.ndarray, current: np.ndarray,
                 n_bins: int = 10) -> float:
    """Compute Population Stability Index between two distributions.

    Args:
        baseline: Baseline data values.
        current: Current data values.
        n_bins: Number of equal-width bins.

    Returns:
        PSI value (0 = stable, > 0.25 = significant drift).
    """
    bins = np.linspace(baseline.min(), baseline.max(), n_bins + 1)
    p, _ = np.histogram(baseline, bins=bins)
    q, _ = np.histogram(current, bins=bins)
    # Normalise to proportions, add epsilon to avoid log(0)
    p = (p + 1e-10) / (p + 1e-10).sum()
    q = (q + 1e-10) / (q + 1e-10).sum()
    return float(np.sum((q - p) * np.log(q / p)))


def check_numeric_drift(baseline: pd.Series, current: pd.Series) -> dict:
    """Run drift tests on a numeric feature.

    Args:
        baseline: Baseline values for the feature.
        current: Current values for the feature.

    Returns:
        Dictionary with drift metrics and alert status.
    """
    psi = compute_psi(baseline.values, current.values)
    ks_stat, ks_pval = ks_2samp(baseline.values, current.values)
    js_dist = jensen_shannon_distance(
        np.histogram(baseline, bins=20, density=True)[0],
        np.histogram(current, bins=20, density=True)[0],
    )
    return {
        "psi": round(psi, 4),
        "psi_alert": psi > 0.25,
        "ks_statistic": round(ks_stat, 4),
        "ks_p_value": round(ks_pval, 6),
        "ks_alert": ks_pval < 0.05,
        "jensen_shannon": round(js_dist, 4),
        "js_alert": js_dist > 0.15,
    }


def check_categorical_drift(baseline: pd.Series, current: pd.Series) -> dict:
    """Run chi-squared test on a categorical feature.

    Args:
        baseline: Baseline values for the feature.
        current: Current values for the feature.

    Returns:
        Dictionary with chi-squared metric and alert status.
    """
    all_cats = sorted(set(baseline.cat.categories) | set(current.cat.categories))
    baseline_counts = baseline.value_counts().reindex(all_cats, fill_value=0).values
    current_counts = current.value_counts().reindex(all_cats, fill_value=0).values
    # Normalise to proportions
    baseline_prop = baseline_counts / baseline_counts.sum()
    current_prop = current_counts / current_counts.sum()
    chi2_stat, chi2_pval = chi2(current_counts, f_exp=baseline_prop * current_counts.sum())
    return {
        "chi2_statistic": round(chi2_stat, 4),
        "chi2_p_value": round(chi2_pval, 6),
        "chi2_alert": chi2_pval < 0.05,
    }
```

### Step 3 — Check model performance drift

Compare prediction distributions and feature attribution over time:

```python
import numpy as np

def check_prediction_drift(baseline_preds: np.ndarray, current_preds: np.ndarray) -> dict:
    """Check for drift in model prediction distributions.

    Args:
        baseline_preds: Predictions from the baseline period.
        current_preds: Predictions from the current period.

    Returns:
        Dictionary with prediction drift metrics.
    """
    psi = compute_psi(baseline_preds, current_preds)
    ks_stat, ks_pval = ks_2samp(baseline_preds, current_preds)
    return {
        "pred_mean_shift": round(float(current_preds.mean() - baseline_preds.mean()), 4),
        "pred_std_ratio": round(float(current_preds.std() / max(baseline_preds.std(), 1e-10)), 4),
        "pred_psi": round(psi, 4),
        "pred_psi_alert": psi > 0.25,
        "pred_ks_p_value": round(ks_pval, 6),
        "pred_ks_alert": ks_pval < 0.05,
    }


def check_feature_attribution_drift(
    model, baseline_X: pd.DataFrame, current_X: pd.DataFrame,
    top_k: int = 10,
) -> dict:
    """Check for drift in feature importance rankings.

    Args:
        model: Trained model with feature_importances_ attribute.
        baseline_X: Baseline feature data.
        current_X: Current feature data.
        top_k: Number of top features to compare.

    Returns:
        Dictionary with feature importance drift metrics.
    """
    # For tree models, compute variance-weighted importances
    baseline_importance = model.feature_importances_ * baseline_X.var().values
    current_importance = model.feature_importances_ * current_X.var().values

    baseline_ranking = np.argsort(-baseline_importance)[:top_k]
    current_ranking = np.argsort(-current_importance)[:top_k]

    # Kendall tau rank correlation
    from scipy.stats import kendalltau
    tau, tau_pval = kendalltau(baseline_ranking, current_ranking)

    return {
        "rank_correlation": round(float(tau), 4),
        "rank_correlation_p_value": round(float(tau_pval), 6),
        "rank_alert": tau < 0.7,  # significant ranking change
        "top_features_baseline": [baseline_X.columns[i] for i in baseline_ranking],
        "top_features_current": [current_X.columns[i] for i in current_ranking],
    }
```

### Step 4 — Check data quality in production

Monitor for null rate increases and unexpected value ranges:

```python
def check_data_quality(current_df: pd.DataFrame, baseline_null_rates: dict,
                       value_ranges: dict) -> dict:
    """Check production data quality against baseline expectations.

    Args:
        current_df: Current production data.
        baseline_null_rates: Dict mapping column -> expected null rate.
        value_ranges: Dict mapping column -> (min, max) expected range.

    Returns:
        Dictionary with quality check results per column.
    """
    issues = {}
    for col in current_df.columns:
        col_issues = {}
        # Null rate check
        actual_null_rate = current_df[col].isna().mean()
        expected_null_rate = baseline_null_rates.get(col, 0.0)
        if actual_null_rate > expected_null_rate * 1.5:  # 50% increase threshold
            col_issues["null_rate_alert"] = True
            col_issues["null_rate_expected"] = round(expected_null_rate, 4)
            col_issues["null_rate_actual"] = round(actual_null_rate, 4)

        # Value range check (numeric columns only)
        if current_df[col].dtype in ("float64", "int64"):
            vmin, vmax = value_ranges.get(col, (None, None))
            if vmin is not None and current_df[col].min() < vmin:
                col_issues["below_min"] = True
                col_issues["min_expected"] = vmin
                col_issues["min_actual"] = round(float(current_df[col].min()), 4)
            if vmax is not None and current_df[col].max() > vmax:
                col_issues["above_max"] = True
                col_issues["max_expected"] = vmax
                col_issues["max_actual"] = round(float(current_df[col].max()), 4)

        if col_issues:
            issues[col] = col_issues

    return issues
```

### Step 5 — Review Azure ML monitoring schedules and recent runs

```bash
# List all monitoring schedules
az ml schedule list \
  --workspace-name <ws> \
  --resource-group <rg> \
  --query "[].{name:name, status:status, trigger:trigger.type, lastRun:lastRunTime}" -o table

# Show a specific schedule
az ml schedule show \
  --name <schedule_name> \
  --workspace-name <ws> \
  --resource-group <rg>

# List recent pipeline runs for a monitoring schedule
az ml job list \
  --workspace-name <ws> \
  --resource-group <rg> \
  --tag "azureml.automatic_job_name=data_drift_monitoring" \
  --query "[].{name:name, status:status, createdTime:properties.createdTime}" -o table

# Get details of a specific monitoring run
az ml job show \
  --name <job_name> \
  --workspace-name <ws> \
  --resource-group <rg> \
  --query "{status:status, metrics:properties.metrics}"
```

---

## Azure ML built-in monitoring

### Data drift monitoring

Azure ML provides built-in data drift monitoring via scheduled pipelines:

```bash
# Create data drift monitoring schedule
az ml schedule create \
  --file aml/mlops/monitoring/data_drift_monitor.yml \
  --name data-drift-monitor \
  --workspace-name <ws> \
  --resource-group <rg> \
  --enabled true
```

The monitoring YAML defines:
- **Target dataset**: the production data store being monitored
- **Baseline dataset**: the reference distribution (must be production data, not training)
- **Drift thresholds**: per-feature thresholds for PSI, KS, or Jensen-Shannon
- **Schedule**: cron expression (e.g., `0 0 * * 1` for weekly on Monday)
- **Alert action**: webhook, email, or pipeline trigger on drift detection

### Model performance monitoring

```bash
# Create model performance monitoring schedule
az ml schedule create \
  --file aml/mlops/monitoring/model_performance_monitor.yml \
  --name model-performance-monitor \
  --workspace-name <ws> \
  --resource-group <rg> \
  --enabled true
```

This monitors prediction distributions and ground-truth metrics (when labels become available) against the baseline performance recorded at deployment time.

### Managing schedules

```bash
# Pause a schedule (useful during maintenance windows)
az ml schedule update --name <schedule> --enabled false \
  --workspace-name <ws> --resource-group <rg>

# Resume a schedule
az ml schedule update --name <schedule> --enabled true \
  --workspace-name <ws> --resource-group <rg>

# Delete a schedule
az ml schedule delete --name <schedule> --yes \
  --workspace-name <ws> --resource-group <rg>
```

---

## Drift thresholds

| Signal type | Metric | Alert threshold | Severity |
|---|---|---|---|
| Jensen-Shannon distance | JS divergence | > 0.15 | Warning |
| Jensen-Shannon distance | JS divergence | > 0.30 | Critical |
| PSI | Population Stability Index | > 0.25 | Warning |
| PSI | Population Stability Index | > 0.50 | Critical |
| KS test | p-value | < 0.05 | Warning |
| KS test | p-value | < 0.01 | Critical |
| Chi-squared | p-value (categorical) | < 0.05 | Warning |
| Chi-squared | p-value (categorical) | < 0.01 | Critical |
| Null rate increase | Ratio vs baseline | > 1.5x | Warning |
| Null rate increase | Ratio vs baseline | > 2.0x | Critical |
| Prediction PSI | PSI on predictions | > 0.25 | Warning |
| Feature importance rank | Kendall tau | < 0.7 | Warning |

---

## Recommended actions on drift detection

1. **Inspect drifting features** — identify which features triggered the alert and whether the shift is explainable (e.g., seasonal, upstream schema change, new entity influx)
2. **Check upstream data sources** — verify no pipeline failures, schema changes, or data source outages occurred
3. **Correlate with business events** — was there a product change, policy update, or market event that explains the shift?
4. **Assess model impact** — if drift is confirmed, run the model on current data and compare metrics against the baseline. If performance degradation > 10%, escalate.
5. **Trigger retraining if sustained > 2 weeks** — transient drift may resolve naturally. Sustained drift indicates the model has become stale and requires retraining with recent data.
6. **Update baseline after retraining** — once a new model is deployed, establish a new monitoring baseline from the first 2-4 weeks of production data.

---

## Endpoint health checklist

Before declaring an endpoint healthy, verify:

- [ ] Endpoint `provisioningState` is `Succeeded`
- [ ] Deployment `provisioningState` is `Succeeded`
- [ ] `requestFailedCount / requestSucceededCount < 0.01` (less than 1% failure rate)
- [ ] No `OutOfMemoryError`, `ConnectionRefused`, or `Timeout` errors in recent logs
- [ ] Response latency under 2s for single-row payloads
- [ ] Traffic routing matches expected configuration (correct deployment receives expected percentage)
- [ ] CPU and memory utilisation under 80% sustained (check Application Insights or deployment metrics)

---

## Evaluation criteria

Before handing off monitoring results or monitoring configuration, verify all of the following:

- [ ] Endpoint health checked: provisioning state is `Succeeded`, failure rate < 1%, no critical errors in logs
- [ ] Data drift computed against a production baseline (not training data) using at least PSI and KS test
- [ ] Drift thresholds applied per the table above — warnings and critical alerts distinguished
- [ ] Model performance drift checked: prediction distribution shift and feature attribution ranking compared
- [ ] Data quality checks run: null rate increases and value range violations flagged
- [ ] Azure ML monitoring schedules reviewed: status, last run time, and any failed runs investigated
- [ ] Seasonal patterns accounted for — false positives from seasonal shifts ruled out
- [ ] New entity proportion considered — null features for new entities not flagged as drift
- [ ] Action plan documented: drifting features identified, upstream sources checked, retraining timeline set if drift sustained > 2 weeks
- [ ] Baseline data source documented and versioned — reproducible for future comparisons
