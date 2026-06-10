"""CLI tool to create or update a managed online endpoint deployment in Azure ML.

Creates the endpoint (idempotent) then deploys the specified model version
to it. Supports blue-green deployments with configurable traffic splitting.

Usage:
    python deploy_endpoint.py \\
        --endpoint-name my-endpoint \\
        --deployment-name my-deployment \\
        --model-name my_model \\
        --model-version 1 \\
        --workspace-name my-workspace \\
        --resource-group my-rg \\
        --environment dev \\
        --instance-count 1

    # Blue-green with 20% traffic to new deployment
    python deploy_endpoint.py \\
        --endpoint-name my-endpoint \\
        --deployment-name canary-deployment \\
        --model-name my_model \\
        --model-version 2 \\
        --workspace-name my-workspace \\
        --resource-group my-rg \\
        --environment qa \\
        --instance-count 1 \\
        --traffic-percent 20

Exit codes:
    0  Deployment succeeded
    1  Deployment failed (endpoint or deployment provisioning error)
    2  Pre-deployment validation failed (model not found, auth error, etc.)
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Valid environment names for D → Q → P promotion
VALID_ENVIRONMENTS = {"dev", "qa", "prod"}


def run_az_command(args: list[str]) -> str:
    """Run an az CLI command and return stdout.

    Args:
        args: List of arguments to pass to the az CLI.

    Returns:
        Standard output from the command.

    Raises:
        RuntimeError: If the command fails.
    """
    cmd = ["az"] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"az command failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def validate_model_exists(
    model_name: str, model_version: int,
    workspace_name: str, resource_group: str,
) -> bool:
    """Check that the specified model version exists in the registry.

    Args:
        model_name: Registered model name.
        model_version: Model version number.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        True if the model version exists, False otherwise.
    """
    query = f"[?version==`{model_version}`].version"
    raw = run_az_command([
        "ml", "model", "list",
        "--name", model_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", query,
        "--output", "json",
    ])
    versions = json.loads(raw)
    return model_version in versions


def create_or_update_endpoint(
    endpoint_name: str, workspace_name: str, resource_group: str,
) -> Dict[str, Any]:
    """Create or update the managed online endpoint (idempotent).

    Args:
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        Endpoint configuration dictionary.
    """
    logger.info("Creating/updating endpoint '%s'...", endpoint_name)
    raw = run_az_command([
        "ml", "online-endpoint", "create",
        "--name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--auth-mode", "key",
        "--output", "json",
    ])
    return json.loads(raw)


def create_deployment(
    endpoint_name: str, deployment_name: str,
    model_name: str, model_version: int,
    workspace_name: str, resource_group: str,
    instance_count: int, traffic_percent: Optional[int],
) -> Dict[str, Any]:
    """Create a new deployment on the endpoint.

    Args:
        endpoint_name: Name of the online endpoint.
        deployment_name: Name of the deployment.
        model_name: Registered model name.
        model_version: Model version number.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.
        instance_count: Number of instances for the deployment.
        traffic_percent: Traffic percentage (None for all traffic).

    Returns:
        Deployment configuration dictionary.
    """
    logger.info("Creating deployment '%s' on endpoint '%s'...", deployment_name, endpoint_name)
    cmd = [
        "ml", "online-deployment", "create",
        "--name", deployment_name,
        "--endpoint-name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--model", f"{model_name}:{model_version}",
        "--instance-count", str(instance_count),
        "--output", "json",
    ]
    if traffic_percent is not None:
        cmd.extend(["--traffic", str(traffic_percent)])
    else:
        cmd.append("--all-traffic")

    raw = run_az_command(cmd)
    return json.loads(raw)


def update_deployment_traffic(
    endpoint_name: str, deployment_name: str,
    workspace_name: str, resource_group: str,
    traffic_percent: int,
) -> Dict[str, Any]:
    """Update traffic allocation for an existing deployment.

    Args:
        endpoint_name: Name of the online endpoint.
        deployment_name: Name of the deployment.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.
        traffic_percent: Traffic percentage to allocate.

    Returns:
        Updated deployment configuration dictionary.
    """
    logger.info("Updating traffic for deployment '%s' to %d%%...", deployment_name, traffic_percent)
    raw = run_az_command([
        "ml", "online-deployment", "update",
        "--name", deployment_name,
        "--endpoint-name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--traffic", str(traffic_percent),
        "--output", "json",
    ])
    return json.loads(raw)


def get_scoring_uri(
    endpoint_name: str, workspace_name: str, resource_group: str,
) -> str:
    """Retrieve the scoring URI for the endpoint.

    Args:
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        The scoring URI string.
    """
    raw = run_az_command([
        "ml", "online-endpoint", "show",
        "--name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", "scoringUri",
        "--output", "tsv",
    ])
    return raw.strip()


def deploy(
    endpoint_name: str,
    deployment_name: str,
    model_name: str,
    model_version: int,
    workspace_name: str,
    resource_group: str,
    environment: str,
    instance_count: int,
    traffic_percent: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute the full deployment workflow.

    Validates the model exists, creates/updates the endpoint, deploys the
    model, and returns the deployment status with the scoring URI.

    Args:
        endpoint_name: Name of the online endpoint.
        deployment_name: Name of the deployment.
        model_name: Registered model name.
        model_version: Model version number.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.
        environment: Target environment (dev, qa, prod).
        instance_count: Number of instances for the deployment.
        traffic_percent: Traffic percentage (None for all traffic).

    Returns:
        Dictionary with deployment status, scoring URI, and configuration.

    Raises:
        RuntimeError: If any step fails.
    """
    result: Dict[str, Any] = {
        "endpoint_name": endpoint_name,
        "deployment_name": deployment_name,
        "model_name": model_name,
        "model_version": model_version,
        "environment": environment,
        "status": "pending",
    }

    # Pre-deployment: validate model exists
    logger.info("Validating model '%s:v%d' in registry...", model_name, model_version)
    if not validate_model_exists(model_name, model_version, workspace_name, resource_group):
        raise RuntimeError(
            f"Model '{model_name}' version {model_version} not found in workspace '{workspace_name}'"
        )
    logger.info("Model validated successfully")

    # Step 1: Create/update endpoint (idempotent)
    endpoint = create_or_update_endpoint(endpoint_name, workspace_name, resource_group)
    result["endpoint_state"] = endpoint.get("provisioningState", "UNKNOWN")

    # Step 2: Create deployment
    deployment = create_deployment(
        endpoint_name, deployment_name,
        model_name, model_version,
        workspace_name, resource_group,
        instance_count, traffic_percent,
    )
    result["deployment_state"] = deployment.get("provisioningState", "UNKNOWN")
    result["status"] = "succeeded"

    # Step 3: Get scoring URI
    result["scoring_uri"] = get_scoring_uri(endpoint_name, workspace_name, resource_group)

    return result


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Create or update a managed online endpoint deployment in Azure ML.",
    )
    parser.add_argument(
        "--endpoint-name", required=True,
        help="Name of the managed online endpoint.",
    )
    parser.add_argument(
        "--deployment-name", required=True,
        help="Name of the deployment.",
    )
    parser.add_argument(
        "--model-name", required=True,
        help="Registered model name in the Azure ML model registry.",
    )
    parser.add_argument(
        "--model-version", required=True, type=int,
        help="Model version number to deploy.",
    )
    parser.add_argument(
        "--workspace-name", required=True,
        help="Azure ML workspace name.",
    )
    parser.add_argument(
        "--resource-group", required=True,
        help="Azure resource group name.",
    )
    parser.add_argument(
        "--environment", required=True, choices=sorted(VALID_ENVIRONMENTS),
        help="Target environment (dev, qa, prod).",
    )
    parser.add_argument(
        "--instance-count", type=int, default=1,
        help="Number of instances for the deployment (default: 1).",
    )
    parser.add_argument(
        "--traffic-percent", type=int, default=None,
        help="Traffic percentage for blue-green deployment. "
        "If omitted, routes all traffic to this deployment.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the deployment CLI."""
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        result = deploy(
            endpoint_name=args.endpoint_name,
            deployment_name=args.deployment_name,
            model_name=args.model_name,
            model_version=args.model_version,
            workspace_name=args.workspace_name,
            resource_group=args.resource_group,
            environment=args.environment,
            instance_count=args.instance_count,
            traffic_percent=args.traffic_percent,
        )

        print(json.dumps(result, indent=2))
        sys.exit(0)

    except RuntimeError as e:
        logger.error("Deployment failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
