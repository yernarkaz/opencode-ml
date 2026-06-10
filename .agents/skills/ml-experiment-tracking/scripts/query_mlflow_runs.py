"""Query MLflow runs from an experiment and display top results by metric.

Connects to an MLflow tracking server (resolved from Azure ML workspace or
an explicit tracking URI) and retrieves the top N runs ranked by a specified
metric. Outputs a formatted table of run ID, metric value, parameters, and
status to stdout.

Usage:
    # Query via Azure ML workspace (requires az CLI login)
    python query_mlflow_runs.py \\
        --experiment-name my-usecase-training \\
        --metric-name test_r2 \\
        --workspace-name my-ml-workspace \\
        --resource-group my-rg

    # Query via explicit tracking URI
    python query_mlflow_runs.py \\
        --experiment-name my-usecase-training \\
        --metric-name avg_average_precision \\
        --tracking-uri https://example.azureml.net/mlflow \\
        --top-n 5

    # Ascending order (e.g. find worst runs)
    python query_mlflow_runs.py \\
        --experiment-name my-usecase-training \\
        --metric-name test_mae \\
        --tracking-uri https://example.azureml.net/mlflow \\
        --order-asc

Exit codes:
    0  Success
    1  Fatal error (missing experiment, connection failure)
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import mlflow
from mlflow.tracking import MlflowClient


def resolve_tracking_uri(
    tracking_uri: Optional[str],
    workspace_name: Optional[str],
    resource_group: Optional[str],
) -> str:
    """Resolve the MLflow tracking URI.

    Priority:
      1. Explicit --tracking-uri argument
      2. Azure ML workspace lookup (requires az CLI login)
      3. MLflow default (local file store)

    Args:
        tracking_uri: Explicit tracking URI if provided.
        workspace_name: Azure ML workspace name for dynamic resolution.
        resource_group: Azure resource group for workspace lookup.

    Returns:
        The resolved tracking URI string.

    Raises:
        ValueError: If workspace lookup is requested but credentials are missing.
    """
    if tracking_uri:
        return tracking_uri

    if workspace_name and resource_group:
        from azure.ai.ml import MLClient
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        ml_client = MLClient(
            credential=credential,
            subscription_id=_get_subscription_id(resource_group),
            resource_group_name=resource_group,
        )
        ws = ml_client.workspaces.get(workspace_name)
        return ws.mlflow_tracking_uri

    return mlflow.get_tracking_uri()


def _get_subscription_id(resource_group: str) -> str:
    """Fetch the subscription ID for a resource group via az CLI.

    Args:
        resource_group: Azure resource group name.

    Returns:
        The subscription ID string.

    Raises:
        RuntimeError: If az CLI is not available or the resource group is not found.
    """
    import subprocess

    result = subprocess.run(
        [
            "az", "group", "show",
            "--name", resource_group,
            "--query", "id", "-o", "tsv",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to resolve subscription for resource group '{resource_group}': "
            f"{result.stderr.strip()}"
        )
    # Output format: /subscriptions/<sub-id>/resourceGroups/<rg>
    sub_id = result.stdout.strip().split("/")[1]
    return sub_id


def query_runs(
    experiment_name: str,
    metric_name: str,
    top_n: int,
    order_asc: bool,
    tracking_uri: Optional[str] = None,
    workspace_name: Optional[str] = None,
    resource_group: Optional[str] = None,
) -> Dict[str, Any]:
    """Query the top N runs from an experiment by a given metric.

    Args:
        experiment_name: Name of the MLflow experiment.
        metric_name: Metric name to rank by.
        top_n: Number of runs to return.
        order_asc: If True, sort ascending (lowest metric first).
        tracking_uri: Explicit tracking URI (overrides workspace lookup).
        workspace_name: Azure ML workspace name for URI resolution.
        resource_group: Azure resource group for workspace lookup.

    Returns:
        Dict with experiment info, run count, and list of run summaries.

    Raises:
        ValueError: If the experiment does not exist.
    """
    uri = resolve_tracking_uri(tracking_uri, workspace_name, resource_group)
    mlflow.set_tracking_uri(uri)

    client = MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(
            f"Experiment '{experiment_name}' not found at tracking URI '{uri}'. "
            "Check the experiment name and tracking URI."
        )

    direction = "ASC" if order_asc else "DESC"
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=[f"metrics.{metric_name} {direction}"],
        max_results=top_n,
    )

    run_summaries: List[Dict[str, Any]] = []
    for run in runs:
        summary = {
            "run_id": run.info.run_id,
            "status": run.info.status,
            "metric_value": run.data.metrics.get(metric_name),
            "params": dict(run.data.params) if run.data.params else {},
            "tags": dict(run.data.tags) if run.data.tags else {},
        }
        run_summaries.append(summary)

    return {
        "experiment_name": experiment_name,
        "experiment_id": experiment.experiment_id,
        "tracking_uri": uri,
        "metric_name": metric_name,
        "order": direction,
        "top_n": top_n,
        "runs_found": len(runs),
        "runs": run_summaries,
    }


def format_table(result: Dict[str, Any]) -> str:
    """Format query results as a readable table string.

    Args:
        result: Output from query_runs().

    Returns:
        Formatted table string.
    """
    lines: List[str] = []
    lines.append(f"Experiment: {result['experiment_name']}")
    lines.append(f"Metric: {result['metric_name']} ({result['order']})")
    lines.append(f"Tracking URI: {result['tracking_uri']}")
    lines.append(f"Runs returned: {result['runs_found']}/{result['top_n']}")
    lines.append("-" * 80)

    if not result["runs"]:
        lines.append("No runs found.")
        return "\n".join(lines)

    # Header
    header = f"{'Run ID':<38} {'Status':<10} {'Metric':>12}  {'Params'}"
    lines.append(header)
    lines.append("-" * 80)

    for run in result["runs"]:
        run_id = run["run_id"][:36]
        status = run["status"]
        metric = (
            f"{run['metric_value']:.4f}"
            if run["metric_value"] is not None
            else "N/A"
        )
        # Compact param display — show up to 3 key params
        params = run.get("params", {})
        param_str = ", ".join(
            f"{k}={v}" for k, v in list(params.items())[:3]
        )
        if len(params) > 3:
            param_str += f" (+{len(params) - 3})"
        lines.append(f"{run_id:<38} {status:<10} {metric:>12}  {param_str}")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query top MLflow runs from an experiment by metric."
    )
    parser.add_argument(
        "--experiment-name",
        required=True,
        help="Name of the MLflow experiment to query",
    )
    parser.add_argument(
        "--metric-name",
        required=True,
        help="Metric name to rank runs by (e.g. test_r2, avg_average_precision)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Number of top runs to return (default: 10)",
    )
    parser.add_argument(
        "--order-asc",
        action="store_true",
        default=False,
        help="Sort ascending (lowest metric first); default is descending",
    )
    parser.add_argument(
        "--tracking-uri",
        default=None,
        help="Explicit MLflow tracking URI (overrides workspace lookup)",
    )
    parser.add_argument(
        "--workspace-name",
        default=None,
        help="Azure ML workspace name (used with --resource-group for URI resolution)",
    )
    parser.add_argument(
        "--resource-group",
        default=None,
        help="Azure resource group (used with --workspace-name for URI resolution)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON instead of formatted table",
    )
    args = parser.parse_args()

    try:
        result = query_runs(
            experiment_name=args.experiment_name,
            metric_name=args.metric_name,
            top_n=args.top_n,
            order_asc=args.order_asc,
            tracking_uri=args.tracking_uri,
            workspace_name=args.workspace_name,
            resource_group=args.resource_group,
        )

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(format_table(result))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
