---
description: Check model monitoring status and set up monitoring for a deployed endpoint. Usage: /monitor <endpoint_name>
---

# Monitor endpoint: $ARGUMENTS

Current repo: !`pwd`
Azure CLI login status: !`az account show --query "{subscription:name, user:user.name}" -o table 2>/dev/null || echo "Not logged in — run: az login"`

## Monitoring workflow

Load the `ml-monitoring` skill and delegate the full monitoring workflow to it.

The skill handles:
- Listing active monitoring schedules for the endpoint
- Checking recent monitoring run results in MLflow
- Analyzing data drift and model performance signals
- Setting up monitoring if not already configured
- Recommending actions on drift detection

Pass `$ARGUMENTS` as the endpoint name to the skill.
