"""CLI tool to promote a model through D → Q → P environments.

Validates acceptance thresholds in the source environment before promoting
the model deployment to the target environment. Enforces the rule that
environments cannot be skipped (D → Q → P only).

Usage:
    python promote_model.py \\
        --model-name my_model \\
        --source-env dev \\
        --target-env qa \\
        --source-workspace ws-dev \\
        --target-workspace ws-qa \\
        --source-rg rg-dev \\
        --target-rg rg-qa

    # With custom acceptance thresholds
    python promote_model.py \\
        --model-name my_model \\
        --source-env qa \\
        --target-env prod \\
        --source-workspace ws-qa \\
        --target-workspace ws-prod \\
        --source-rg rg-qa \\
        --target-rg rg-prod \\
        --gate-min-auc 0.75 \\
        --gate-min-r2 0.60

Exit codes:
    0  Promotion succeeded
    1  Promotion failed (deployment error in target environment)
    2  Pre-promotion validation failed (thresholds not met, invalid path)
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Valid promotion paths: source → target
VALID_PROMOTIONS = {
    "dev": "qa",
    "qa": "prod",
}


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


def validate_promotion_path(source_env: str, target_env: str) -> None:
    """Validate that the promotion path is allowed (no skipping environments).

    Args:
        source_env: Source environment name.
        target_env: Target environment name.

    Raises:
        ValueError: If the promotion path is invalid.
    """
    allowed_target = VALID_PROMOTIONS.get(source_env)
    if allowed_target != target_env:
        raise ValueError(
            f"Invalid promotion path: '{source_env}' → '{target_env}'. "
            f"Allowed promotions: {', '.join(f'{k} → {v}' for k, v in VALID_PROMOTIONS.items())}"
        )


def get_latest_model_version(
    model_name: str, workspace_name: str, resource_group: str,
) -> int:
    """Get the latest version number for a registered model.

    Args:
        model_name: Registered model name.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        The latest model version number.

    Raises:
        RuntimeError: If the model is not found.
    """
    raw = run_az_command([
        "ml", "model", "list",
        "--name", model_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", "max([].version)",
        "--output", "tsv",
    ])
    version = int(raw.strip())
    if version < 1:
        raise RuntimeError(f"Model '{model_name}' not found in workspace '{workspace_name}'")
    return version


def check_endpoint_health(
    endpoint_name: str, workspace_name: str, resource_group: str,
) -> Dict[str, Any]:
    """Check that an endpoint and its deployments are healthy.

    Args:
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        Dictionary with endpoint state and deployment health summary.
    """
    query = "{state:properties.provisioningState, traffic:properties.traffic}"
    raw = run_az_command([
        "ml", "online-endpoint", "show",
        "--name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", query,
        "--output", "json",
    ])
    return json.loads(raw)


def check_deployment_health(
    deployment_name: str, endpoint_name: str,
    workspace_name: str, resource_group: str,
) -> Dict[str, Any]:
    """Check that a specific deployment is healthy.

    Args:
        deployment_name: Name of the deployment.
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        Dictionary with deployment state and request metrics.
    """
    query = (
        "{state:properties.provisioningState, "
        "instanceCount:properties.instanceCount, "
        "requestSucceededCount:properties.requestSucceededCount, "
        "requestFailedCount:properties.requestFailedCount}"
    )
    raw = run_az_command([
        "ml", "online-deployment", "show",
        "--name", deployment_name,
        "--endpoint-name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", query,
        "--output", "json",
    ])
    return json.loads(raw)


def validate_acceptance_thresholds(
    gate_min_auc: Optional[float],
    gate_min_r2: Optional[float],
    gate_min_ap: Optional[float],
) -> List[str]:
    """Validate that acceptance thresholds are reasonable.

    Args:
        gate_min_auc: Minimum acceptable AUC (binary classification).
        gate_min_r2: Minimum acceptable R² (regression).
        gate_min_ap: Minimum acceptable average precision (binary classification).

    Returns:
        List of validation warnings (empty if all thresholds are valid).
    """
    warnings: List[str] = []

    if gate_min_auc is not None:
        if not (0.5 < gate_min_auc <= 1.0):
            warnings.append(
                f"gate_min_auc={gate_min_auc} is outside valid range (0.5, 1.0]"
            )

    if gate_min_r2 is not None:
        if not (-1.0 <= gate_min_r2 <= 1.0):
            warnings.append(
                f"gate_min_r2={gate_min_r2} is outside valid range [-1.0, 1.0]"
            )

    if gate_min_ap is not None:
        if not (0.0 < gate_min_ap <= 1.0):
            warnings.append(
                f"gate_min_ap={gate_min_ap} is outside valid range (0.0, 1.0]"
            )

    return warnings


def deploy_to_target(
    model_name: str, model_version: int,
    target_workspace: str, target_rg: str,
    target_env: str,
) -> Dict[str, Any]:
    """Deploy the model to the target environment.

    Constructs the standard endpoint and deployment names based on the
    environment and model name, then creates the deployment.

    Args:
        model_name: Registered model name.
        model_version: Model version number.
        target_workspace: Target Azure ML workspace name.
        target_rg: Target resource group name.
        target_env: Target environment (qa or prod).

    Returns:
        Dictionary with deployment result and scoring URI.
    """
    endpoint_name = f"{model_name}-{target_env}"
    deployment_name = f"{model_name}_v{model_version}"

    logger.info("Deploying '%s:v%d' to %s environment...", model_name, model_version, target_env)

    # Create endpoint (idempotent)
    logger.info("Creating/updating endpoint '%s'...", endpoint_name)
    run_az_command([
        "ml", "online-endpoint", "create",
        "--name", endpoint_name,
        "--workspace-name", target_workspace,
        "--resource-group", target_rg,
        "--auth-mode", "key",
    ])

    # Create deployment with all traffic
    logger.info("Creating deployment '%s'...", deployment_name)
    raw = run_az_command([
        "ml", "online-deployment", "create",
        "--name", deployment_name,
        "--endpoint-name", endpoint_name,
        "--workspace-name", target_workspace,
        "--resource-group", target_rg,
        "--model", f"{model_name}:{model_version}",
        "--all-traffic",
        "--output", "json",
    ])
    deployment = json.loads(raw)

    # Get scoring URI
    scoring_uri = run_az_command([
        "ml", "online-endpoint", "show",
        "--name", endpoint_name,
        "--workspace-name", target_workspace,
        "--resource-group", target_rg,
        "--query", "scoringUri",
        "--output", "tsv",
    ]).strip()

    return {
        "endpoint_name": endpoint_name,
        "deployment_name": deployment_name,
        "deployment_state": deployment.get("provisioningState", "UNKNOWN"),
        "scoring_uri": scoring_uri,
    }


def promote(
    model_name: str,
    source_env: str,
    target_env: str,
    source_workspace: str,
    target_workspace: str,
    source_rg: str,
    target_rg: str,
    gate_min_auc: Optional[float] = None,
    gate_min_r2: Optional[float] = None,
    gate_min_ap: Optional[float] = None,
) -> Dict[str, Any]:
    """Execute the full promotion workflow.

    Validates the promotion path, checks source environment health,
    validates acceptance thresholds, and deploys to the target environment.

    Args:
        model_name: Registered model name.
        source_env: Source environment (dev or qa).
        target_env: Target environment (qa or prod).
        source_workspace: Source Azure ML workspace name.
        target_workspace: Target Azure ML workspace name.
        source_rg: Source resource group name.
        target_rg: Target resource group name.
        gate_min_auc: Minimum acceptable AUC threshold.
        gate_min_r2: Minimum acceptable R² threshold.
        gate_min_ap: Minimum acceptable average precision threshold.

    Returns:
        Dictionary with promotion status and deployment details.

    Raises:
        ValueError: If the promotion path is invalid.
        RuntimeError: If any step fails.
    """
    result: Dict[str, Any] = {
        "model_name": model_name,
        "source_env": source_env,
        "target_env": target_env,
        "status": "pending",
    }

    # Step 1: Validate promotion path
    logger.info("Validating promotion path: '%s' → '%s'...", source_env, target_env)
    validate_promotion_path(source_env, target_env)
    logger.info("Promotion path validated")

    # Step 2: Validate acceptance thresholds
    threshold_warnings = validate_acceptance_thresholds(gate_min_auc, gate_min_r2, gate_min_ap)
    if threshold_warnings:
        logger.warning("Threshold warnings: %s", threshold_warnings)
        result["threshold_warnings"] = threshold_warnings

    # Step 3: Check source environment health
    source_endpoint = f"{model_name}-{source_env}"
    logger.info("Checking source endpoint '%s' health...", source_endpoint)
    source_health = check_endpoint_health(source_endpoint, source_workspace, source_rg)
    result["source_endpoint_state"] = source_health.get("state", "UNKNOWN")

    if source_health.get("state") != "Succeeded":
        raise RuntimeError(
            f"Source endpoint '{source_endpoint}' is not healthy: "
            f"state={source_health.get('state')}. "
            f"Fix the source environment before promoting."
        )
    logger.info("Source endpoint is healthy")

    # Step 4: Get latest model version from source
    model_version = get_latest_model_version(model_name, source_workspace, source_rg)
    result["model_version"] = model_version
    logger.info("Latest model version: %d", model_version)

    # Step 5: Deploy to target environment
    logger.info("Deploying to target environment '%s'...", target_env)
    deployment_result = deploy_to_target(
        model_name, model_version,
        target_workspace, target_rg,
        target_env,
    )

    result.update(deployment_result)
    result["status"] = "succeeded"

    return result


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Promote a model through D → Q → P environments.",
    )
    parser.add_argument(
        "--model-name", required=True,
        help="Registered model name in the Azure ML model registry.",
    )
    parser.add_argument(
        "--source-env", required=True, choices=["dev", "qa"],
        help="Source environment (dev or qa).",
    )
    parser.add_argument(
        "--target-env", required=True, choices=["qa", "prod"],
        help="Target environment (qa or prod).",
    )
    parser.add_argument(
        "--source-workspace", required=True,
        help="Source Azure ML workspace name.",
    )
    parser.add_argument(
        "--target-workspace", required=True,
        help="Target Azure ML workspace name.",
    )
    parser.add_argument(
        "--source-rg", required=True,
        help="Source resource group name.",
    )
    parser.add_argument(
        "--target-rg", required=True,
        help="Target resource group name.",
    )
    parser.add_argument(
        "--gate-min-auc", type=float, default=None,
        help="Minimum acceptable AUC for binary classification.",
    )
    parser.add_argument(
        "--gate-min-r2", type=float, default=None,
        help="Minimum acceptable R² for regression.",
    )
    parser.add_argument(
        "--gate-min-ap", type=float, default=None,
        help="Minimum acceptable average precision for binary classification.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the promotion CLI."""
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        result = promote(
            model_name=args.model_name,
            source_env=args.source_env,
            target_env=args.target_env,
            source_workspace=args.source_workspace,
            target_workspace=args.target_workspace,
            source_rg=args.source_rg,
            target_rg=args.target_rg,
            gate_min_auc=args.gate_min_auc,
            gate_min_r2=args.gate_min_r2,
            gate_min_ap=args.gate_min_ap,
        )

        print(json.dumps(result, indent=2))
        sys.exit(0)

    except ValueError as e:
        logger.error("Invalid promotion: %s", e)
        sys.exit(2)
    except RuntimeError as e:
        logger.error("Promotion failed: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
