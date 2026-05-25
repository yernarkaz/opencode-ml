---
description: Deploy a trained model to an Azure ML endpoint. Usage: /deploy <model_name> <version>
---

# Deploy model to Azure ML: $ARGUMENTS

Current repo: !`pwd`
Git branch: !`git branch --show-current 2>/dev/null`
Azure CLI login status: !`az account show --query "{subscription:name, user:user.name}" -o table 2>/dev/null || echo "Not logged in — run: az login"`

Pre-deployment checklist — verify each item before proceeding:

1. **Azure login** — confirm `az account show` returns the correct subscription
2. **Model exists in registry** — `az ml model list --name <model_name> --workspace-name <ws> --resource-group <rg>`
3. **Endpoint definition** — confirm `aml/mlops/definitions/endpoint_inference.yml` is correct
4. **Deployment definition** — confirm `aml/mlops/definitions/deployment_inference.yml` references the right model version
5. **Environment** — confirm `aml/mlops/definitions/environment.yml` dependencies are up to date
6. **Tests pass** — `pytest tests/unit/ --verbose --tb=short`

Deployment sequence (D → Q → P):

```bash
# Dev environment first
az ml online-endpoint create -f aml/mlops/definitions/endpoint_inference.yml --workspace-name <ws-dev>
az ml online-deployment create -f aml/mlops/definitions/deployment_inference.yml --workspace-name <ws-dev>

# Validate in dev before promoting to QA
az ml online-endpoint invoke --name <endpoint> --request-file <test_payload> --workspace-name <ws-dev>
```

After deployment to each environment:

- Run smoke test with a sample payload
- Confirm predictions are non-null and within expected range
- Check endpoint logs for errors: `az ml online-endpoint get-logs --name <endpoint>`

Do not deploy to P (prod) without explicit confirmation that D and Q are healthy.

Refer to `docs/experiment-conventions.md` for environment naming and model registry format.
