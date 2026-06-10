"""CLI tool to check Azure ML online endpoint health.

Accepts endpoint, workspace, and resource group arguments, then queries
the Azure ML REST API (via az CLI) to report endpoint status, deployment
health, and recent error rates.

Usage:
    python check_endpoint_health.py \
        --endpoint-name my-endpoint \
        --workspace-name my-workspace \
        --resource-group my-rg
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)


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
        cmd, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"az command failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def get_endpoint_status(
    endpoint_name: str, workspace_name: str, resource_group: str,
) -> dict[str, Any]:
    """Fetch endpoint provisioning state and traffic configuration.

    Args:
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        Dictionary with endpoint status fields.
    """
    query = "{state:properties.provisioningState, traffic:properties.traffic, authMode:properties.authMode}"
    raw = run_az_command([
        "ml", "online-endpoint", "show",
        "--name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", query,
        "--output", "json",
    ])
    return json.loads(raw)


def get_deployment_status(
    deployment_name: str, endpoint_name: str,
    workspace_name: str, resource_group: str,
) -> dict[str, Any]:
    """Fetch deployment health and request metrics.

    Args:
        deployment_name: Name of the deployment.
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        Dictionary with deployment status fields.
    """
    query = (
        "{state:properties.provisioningState, "
        "instanceCount:properties.instanceCount, "
        "requestCount:properties.requestCount, "
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


def get_deployments_for_endpoint(
    endpoint_name: str, workspace_name: str, resource_group: str,
) -> list[str]:
    """List deployment names for an endpoint.

    Args:
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.

    Returns:
        List of deployment names.
    """
    raw = run_az_command([
        "ml", "online-deployment", "list",
        "--endpoint-name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--query", "[].name",
        "--output", "json",
    ])
    return json.loads(raw)


def get_recent_logs(
    deployment_name: str, endpoint_name: str,
    workspace_name: str, resource_group: str,
    lines: int = 100,
) -> str:
    """Fetch recent deployment logs.

    Args:
        deployment_name: Name of the deployment.
        endpoint_name: Name of the online endpoint.
        workspace_name: Azure ML workspace name.
        resource_group: Azure resource group name.
        lines: Number of log lines to retrieve.

    Returns:
        Log text from the deployment.
    """
    return run_az_command([
        "ml", "online-deployment", "get-logs",
        "--name", deployment_name,
        "--endpoint-name", endpoint_name,
        "--workspace-name", workspace_name,
        "--resource-group", resource_group,
        "--lines", str(lines),
    ])


def check_error_patterns(logs: str) -> list[str]:
    """Scan deployment logs for known error patterns.

    Args:
        logs: Raw log text from the deployment.

    Returns:
        List of error patterns found in the logs.
    """
    error_patterns = [
        "OutOfMemoryError",
        "ConnectionRefused",
        "Timeout",
        "Killed",
        "OOMKilled",
        "CRASH",
        "FATAL",
    ]
    found = []
    for line in logs.splitlines():
        for pattern in error_patterns:
            if pattern.lower() in line.lower():
                found.append(f"[{pattern}] {line.strip()}")
    return found


def format_health_report(
    endpoint: dict[str, Any],
    deployments: dict[str, dict[str, Any]],
    log_errors: dict[str, list[str]],
) -> str:
    """Format a human-readable health report.

    Args:
        endpoint: Endpoint status dictionary.
        deployments: Mapping of deployment name to status dictionary.
        log_errors: Mapping of deployment name to list of error lines.

    Returns:
        Formatted health report string.
    """
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  ENDPOINT HEALTH REPORT")
    lines.append("=" * 60)

    # Endpoint summary
    lines.append(f"\nEndpoint state: {endpoint.get('state', 'UNKNOWN')}")
    lines.append(f"Auth mode:      {endpoint.get('authMode', 'UNKNOWN')}")
    traffic = endpoint.get("traffic", {})
    if traffic:
        lines.append(f"Traffic config: {json.dumps(traffic)}")

    # Deployment summaries
    for dep_name, dep in deployments.items():
        lines.append(f"\n--- Deployment: {dep_name} ---")
        lines.append(f"  State:           {dep.get('state', 'UNKNOWN')}")
        lines.append(f"  Instances:       {dep.get('instanceCount', 'N/A')}")

        succeeded = dep.get("requestSucceededCount", 0) or 0
        failed = dep.get("requestFailedCount", 0) or 0
        total = succeeded + failed

        if total > 0:
            failure_rate = failed / total * 100
            lines.append(f"  Requests:        {total} total ({succeeded} ok, {failed} failed)")
            lines.append(f"  Failure rate:    {failure_rate:.2f}%")
            if failure_rate > 1.0:
                lines.append(f"  WARNING: Failure rate {failure_rate:.2f}% exceeds 1% threshold")
        else:
            lines.append(f"  Requests:        No traffic recorded")

        # Log errors
        errors = log_errors.get(dep_name, [])
        if errors:
            lines.append(f"  Log errors:      {len(errors)} error pattern(s) found")
            for err in errors[:5]:  # Show up to 5
                lines.append(f"    - {err}")
            if len(errors) > 5:
                lines.append(f"    ... and {len(errors) - 5} more")
        else:
            lines.append(f"  Log errors:      None")

    # Overall verdict
    lines.append("\n" + "=" * 60)
    all_healthy = (
        endpoint.get("state") == "Succeeded"
        and all(d.get("state") == "Succeeded" for d in deployments.values())
        and all(len(errs) == 0 for errs in log_errors.values())
    )
    if all_healthy:
        lines.append("  VERDICT: HEALTHY")
    else:
        lines.append("  VERDICT: ISSUES DETECTED — review warnings above")
    lines.append("=" * 60)

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Check Azure ML online endpoint health.",
    )
    parser.add_argument(
        "--endpoint-name", required=True,
        help="Name of the managed online endpoint.",
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
        "--deployment-name", default=None,
        help="Specific deployment to check. If omitted, checks all deployments.",
    )
    parser.add_argument(
        "--log-lines", type=int, default=100,
        help="Number of recent log lines to scan (default: 100).",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the endpoint health check CLI."""
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        # Fetch endpoint status
        logger.info("Fetching endpoint status for '%s'...", args.endpoint_name)
        endpoint = get_endpoint_status(
            args.endpoint_name, args.workspace_name, args.resource_group,
        )

        # Determine which deployments to check
        if args.deployment_name:
            deployment_names = [args.deployment_name]
        else:
            deployment_names = get_deployments_for_endpoint(
                args.endpoint_name, args.workspace_name, args.resource_group,
            )

        if not deployment_names:
            print("No deployments found for this endpoint.")
            sys.exit(1)

        # Fetch deployment statuses and logs
        deployments: dict[str, dict[str, Any]] = {}
        log_errors: dict[str, list[str]] = {}

        for dep_name in deployment_names:
            logger.info("Checking deployment '%s'...", dep_name)
            deployments[dep_name] = get_deployment_status(
                dep_name, args.endpoint_name,
                args.workspace_name, args.resource_group,
            )
            logs = get_recent_logs(
                dep_name, args.endpoint_name,
                args.workspace_name, args.resource_group,
                lines=args.log_lines,
            )
            log_errors[dep_name] = check_error_patterns(logs)

        # Print report
        report = format_health_report(endpoint, deployments, log_errors)
        print(report)

        # Exit with non-zero if issues detected
        all_healthy = (
            endpoint.get("state") == "Succeeded"
            and all(d.get("state") == "Succeeded" for d in deployments.values())
            and all(len(errs) == 0 for errs in log_errors.values())
        )
        sys.exit(0 if all_healthy else 1)

    except RuntimeError as e:
        logger.error("Failed to check endpoint health: %s", e)
        sys.exit(2)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
