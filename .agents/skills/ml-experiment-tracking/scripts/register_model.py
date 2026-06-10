"""Register a trained model in the MLflow model registry.

Loads a model artifact from a local path or an MLflow run URI and registers
it under a specified name in the MLflow model registry. Supports both local
tracking servers and Azure ML workspaces.

Usage:
    # Register from a local model path
    python register_model.py \\
        --model-name my-usecase_model_v1 \\
        --model-path ./artifacts/model \\
        --tracking-uri https://example.azureml.net/mlflow

    # Register from an MLflow run URI
    python register_model.py \\
        --model-name my-usecase_model_v1 \\
        --run-id abc123def456 \\
        --workspace-name my-ml-workspace \\
        --resource-group my-rg

    # Register with a custom artifact path within the run
    python register_model.py \\
        --model-name my-usecase_model_v1 \\
        --run-id abc123def456 \\
        --model-path model \\
        --workspace-name my-ml-workspace \\
        --resource-group my-rg

Exit codes:
    0  Model registered successfully
    1  Fatal error (missing run, connection failure, registration error)
"""

import argparse
import json
import sys
from typing import Optional

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
    sub_id = result.stdout.strip().split("/")[1]
    return sub_id


def register_model(
    model_name: str,
    model_uri: str,
    tracking_uri: Optional[str] = None,
    workspace_name: Optional[str] = None,
    resource_group: Optional[str] = None,
) -> dict:
    """Register a model in the MLflow model registry.

    Args:
        model_name: Name for the registered model (e.g. 'my-usecase_model_v1').
        model_uri: URI of the model artifact. Can be a local path,
            'runs:/<run_id>/artifact_path', or 'models:/<name>/<version>'.
        tracking_uri: Explicit tracking URI (overrides workspace lookup).
        workspace_name: Azure ML workspace name for URI resolution.
        resource_group: Azure resource group for workspace lookup.

    Returns:
        Dict with registration details including model URI and version.

    Raises:
        ValueError: If the model URI is invalid or the run does not exist.
    """
    uri = resolve_tracking_uri(tracking_uri, workspace_name, resource_group)
    mlflow.set_tracking_uri(uri)

    client = MlflowClient(tracking_uri_uri=uri)

    # Register the model
    result = client.create_registered_model_if_not_exists(model_name)

    # Log the model to get a version
    mv = client.create_model_version(
        name=model_name,
        source=model_uri,
        run_id=None,  # Will be auto-detected from runs:/ URIs
    )

    # If the URI is runs:/ format, extract the run_id for the run_id field
    run_id = None
    if model_uri.startswith("runs:/"):
        parts = model_uri.split("/")
        run_id = parts[2] if len(parts) > 2 else None

    return {
        "model_name": model_name,
        "model_version": mv.version,
        "model_uri": f"models:/{model_name}/{mv.version}",
        "source": model_uri,
        "run_id": run_id,
        "tracking_uri": uri,
        "status": mv.status,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Register a model in the MLflow model registry."
    )
    parser.add_argument(
        "--model-name",
        required=True,
        help="Name for the registered model (e.g. my-usecase_model_v1)",
    )
    parser.add_argument(
        "--model-path",
        default=None,
        help="Local path to the model artifact directory",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="MLflow run ID (used with --model-path to form runs:/ URI)",
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
    args = parser.parse_args()

    # Build the model URI
    if args.run_id and args.model_path:
        model_uri = f"runs:/{args.run_id}/{args.model_path}"
    elif args.model_path:
        model_uri = args.model_path
    elif args.run_id:
        model_uri = f"runs:/{args.run_id}/model"
    else:
        parser.error(
            "Either --model-path or --run-id (or both) must be provided."
        )

    try:
        result = register_model(
            model_name=args.model_name,
            model_uri=model_uri,
            tracking_uri=args.tracking_uri,
            workspace_name=args.workspace_name,
            resource_group=args.resource_group,
        )

        print(json.dumps(result, indent=2))
        print(
            f"\nModel registered successfully: {result['model_uri']}",
            file=sys.stderr,
        )

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
