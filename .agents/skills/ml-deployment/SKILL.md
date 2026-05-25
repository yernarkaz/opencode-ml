---
name: ml-deployment
description: >
  Use this skill when deploying a trained model to Azure ML, creating or updating online
  endpoints, or promoting through D → Q → P environments for any ML repo.
  Also use for scoring script changes, pre-deployment validation, post-deployment health
  checks, or triggering Azure DevOps deployment pipelines. Do NOT use for training
  (use ml-model-development) or for evaluating whether a model is ready to deploy
  (use ml-evaluation first). Trigger on: "deploy the model", "create endpoint",
  "promote to QA", "promote to production", "scoring script", "deployment failed",
  "check endpoint health", "update deployment", or any mention of
  az ml online-endpoint, deployment_inference.yml, or D→Q→P promotion.
compatibility: opencode
metadata:
  stage: deployment
  repos: <your-repo-name>
---

# ML Deployment Skill

## When to load this skill
Load when the task involves: deploying a trained model to Azure ML, creating or updating online endpoints, promoting through D → Q → P environments, scoring script changes, or post-deployment validation.

---

## Gotchas

- **`az ml online-deployment create` without `--all-traffic` routes 0% of requests to the new deployment.** The deployment is created successfully but all traffic continues to the old one. Always include `--all-traffic` unless you are intentionally doing a canary deployment.
- **`az ml online-deployment create` is NOT idempotent.** Re-running the command creates a second deployment alongside the first. Use `az ml online-deployment update` to modify an existing deployment.
- **`os.environ["AZUREML_MODEL_DIR"]` may have a trailing slash on some AML runtime versions.** Always use `os.path.join(os.environ["AZUREML_MODEL_DIR"], "model.pkl")` — never string concatenation.
- **D → Q → P is policy-enforced but not fully gated.** Azure DevOps pipeline policies prevent direct P promotion, but nothing stops you from deploying to Q before D is fully tested. Always test D manually before proceeding — the pipelines do not enforce this for you.
- **Endpoint creation is idempotent; deployment creation is not.** `az ml online-endpoint create` is safe to re-run (no-op if it already exists). `az ml online-deployment create` is not — it will create a parallel deployment. Know which command you are running.

---

## Deployment architecture

All repos follow the same deployment pattern:

```
Azure ML Model Registry
  → Online Endpoint (managed, serverless)
    → Deployment (blue/green)
      → D environment → Q environment → P environment
```

Definitions live in `aml/mlops/definitions/`:
```
endpoint_inference.yml      — endpoint spec (name, auth mode)
deployment_inference.yml    — deployment spec (model, environment, compute, scoring script)
environment.yml             — conda/pip environment
```

---

## Pre-deployment checklist

```bash
# 1. Confirm Azure login and correct subscription
az account show --query "{sub:name, user:user.name}" -o table

# 2. Confirm model exists in registry
az ml model list \
  --name <model_name> \
  --workspace-name <ws> \
  --resource-group <rg> \
  --query "[].{version:version, created:createdTime}" -o table

# 3. Run unit tests
pytest tests/unit/ --verbose --tb=short

# 4. Validate component arguments (if pipeline was changed)
pytest tests/integration/test_component_argument_validation.py -v

# 5. Confirm scoring script handles edge cases
python aml/api/test_score_local.py
```

---

## Endpoint creation

```bash
# Create endpoint (idempotent — safe to re-run)
az ml online-endpoint create \
  --file aml/mlops/definitions/endpoint_inference.yml \
  --workspace-name <ws-dev> \
  --resource-group <rg>

# Create deployment
az ml online-deployment create \
  --file aml/mlops/definitions/deployment_inference.yml \
  --workspace-name <ws-dev> \
  --resource-group <rg> \
  --all-traffic  # route 100% traffic to this deployment
```

---

## D → Q → P promotion sequence

**Never skip an environment.** Each environment must be validated before promotion.

```bash
# === DEV ===
az ml online-endpoint create -f endpoint_inference.yml --workspace-name <ws-dev>
az ml online-deployment create -f deployment_inference.yml --workspace-name <ws-dev>
# Smoke test
az ml online-endpoint invoke \
  --name <endpoint> \
  --request-file tests/sample_payload.json \
  --workspace-name <ws-dev>

# === QA (only after dev is healthy) ===
az ml online-deployment create -f deployment_inference.yml --workspace-name <ws-qa>
# Run full validation suite against QA endpoint

# === PROD (only after QA is healthy, with explicit confirmation) ===
az ml online-deployment create -f deployment_inference.yml --workspace-name <ws-prod>
```

---

## Scoring script pattern

```python
# score.py — standard AML online endpoint scoring script
import json
import logging
import os
import pickle
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def init():
    """Load model from AML_MODEL_DIR on endpoint startup."""
    global model
    model_path = os.path.join(os.environ["AZUREML_MODEL_DIR"], "model.pkl")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    logger.info("Model loaded successfully")


def run(raw_data: str) -> str:
    """Score a single request.

    Args:
        raw_data: JSON string with input features.

    Returns:
        JSON string with predictions.
    """
    try:
        data = json.loads(raw_data)
        df = pd.DataFrame(data["data"])
        predictions = model.predict(df)
        return json.dumps({"predictions": predictions.tolist()})
    except Exception as e:
        logger.error(f"Scoring failed: {e}")
        return json.dumps({"error": str(e)})
```

---

## Post-deployment validation

```bash
# Check endpoint health
az ml online-endpoint show \
  --name <endpoint> \
  --workspace-name <ws> \
  --query "{state:properties.provisioningState, traffic:properties.traffic}"

# Get recent logs
az ml online-deployment get-logs \
  --name <deployment> \
  --endpoint-name <endpoint> \
  --workspace-name <ws> \
  --lines 100

# Invoke with test payload
az ml online-endpoint invoke \
  --name <endpoint> \
  --request-file tests/sample_payload.json \
  --workspace-name <ws>
```

Validation checks after deployment:
- Response is non-null JSON
- Prediction values are within expected range (non-negative, within historical bounds)
- Response latency < 2s for a single-row payload
- No error lines in deployment logs

---

## Triggering via Azure DevOps pipeline

```bash
# Trigger deployment pipelines (D environment only — Q and P gate automatically)
az pipelines run --name "deploy-training" --branch main
az pipelines run --name "deploy-inference" --branch main
```

Pipeline IDs available via: `az pipelines list --query "[].{id:id, name:name}" -o table`

---

## Evaluation criteria

Before handing off deployment steps or deployment code, verify all of the following:

- [ ] Pre-deployment checklist completed: Azure login confirmed, model exists in registry, unit tests pass, scoring script edge-case test passes
- [ ] Component argument validation run if any YAML or argparse changes were made: `pytest tests/integration/test_component_argument_validation.py -v`
- [ ] D environment deployed and smoke-tested before QA promotion — never skipped
- [ ] QA environment validated with full validation suite before PROD promotion — never skipped
- [ ] Endpoint creation command uses `--file` pointing to `aml/mlops/definitions/endpoint_inference.yml`
- [ ] Deployment uses `--all-traffic` flag when routing all traffic to new deployment
- [ ] Scoring script `init()` loads model from `os.environ["AZUREML_MODEL_DIR"]` — not from hardcoded path
- [ ] Scoring script `run()` wraps logic in `try/except` and returns `{"error": str(e)}` on failure
- [ ] Post-deployment validation performed: endpoint state is `Succeeded`, no errors in logs, test payload response is non-null JSON within expected range
- [ ] Response latency < 2s confirmed for single-row payload
- [ ] Pipeline IDs confirmed via `az pipelines list` before triggering ADO deployment pipelines
