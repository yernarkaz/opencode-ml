---
description: Clean up old autoresearch branches, stale MLflow runs, caches, and show disk usage. Usage: /cleanup
---

# Repo cleanup

Current repo: !`pwd`

## Cleanup steps

Run these steps sequentially. Confirm with the user before destructive operations (branch deletion, MLflow run deletion).

### 1. Clean up old autoresearch branches

```bash
# List autoresearch branches (oldest first)
git branch --list 'autoresearch/*' --sort=committerdate

# Delete merged autoresearch branches (interactive confirmation)
git branch --list 'autoresearch/*' | xargs -I {} git branch -d {} 2>/dev/null || true
```

### 2. Remove stale MLflow runs

```bash
# Query failed/aborted runs in the experiment
mlflow searches-runs --experiment-name <experiment> --filter-tags status=FAILED
# Or via Python:
python -c "
import mlflow
client = mlflow.tracking.MlflowClient()
runs = client.search_runs(experiment_ids=['<exp_id>'], filter_string='tags.mlflow.run.status IN (\"FAILED\", \"ABORTED\")')
print(f'Found {len(runs)} stale runs')
for r in runs:
    client.delete_run(r.info.run_id)
    print(f'  Deleted {r.info.run_id}')
"
```

### 3. Clear Python caches

```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
rm -rf .mypy_cache 2>/dev/null || true
```

### 4. Compact git history (optional)

```bash
# Only if repo size is bloated — confirm with user first
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

### 5. Disk usage summary

```bash
echo "=== Disk usage ==="
du -sh .git/ 2>/dev/null
du -sh aml/ 2>/dev/null
du -sh data/ 2>/dev/null
du -sh models/ 2>/dev/null
echo "=== Total repo ==="
du -sh .
```
