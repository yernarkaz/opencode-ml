"""Query MLflow for experiment runs, metrics, and parameters. Returns JSON.

PEP 723 inline dependencies — run with: uv run run-mlflow-query.py --experiment_name my-usecase-training
The MLflow tracking URI must be set in the environment (MLFLOW_TRACKING_URI) or via
--tracking_uri argument.
"""

# /// script
# dependencies = [
#   "mlflow>=2.10",
#   "azure-ai-ml>=1.13",
#   "azure-identity>=1.15",
# ]
# ///

import argparse
import json
import os
import sys
import logging

logger = logging.getLogger(__name__)


def _resolve_tracking_uri(tracking_uri: str | None) -> str:
    """Resolve MLflow tracking URI from arg, env var, or AML workspace."""
    if tracking_uri:
        return tracking_uri

    env_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if env_uri:
        return env_uri

    raise ValueError(
        "MLflow tracking URI not found. Set MLFLOW_TRACKING_URI environment variable "
        "or pass --tracking_uri. To resolve from AML workspace:\n"
        "  az ml workspace show --name <ws> --resource-group <rg> --query mlflowTrackingUri -o tsv"
    )


def query_runs(
    experiment_name: str | None,
    run_id: str | None,
    order_by_metric: str | None,
    top_n: int,
    tracking_uri: str | None,
) -> dict:
    import mlflow
    from mlflow.tracking import MlflowClient

    uri = _resolve_tracking_uri(tracking_uri)
    mlflow.set_tracking_uri(uri)
    client = MlflowClient()

    if run_id:
        run = client.get_run(run_id)
        return {
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "status": run.info.status,
            "start_time": run.info.start_time,
            "end_time": run.info.end_time,
            "metrics": dict(run.data.metrics),
            "params": dict(run.data.params),
            "tags": {
                k: v for k, v in run.data.tags.items() if not k.startswith("mlflow.")
            },
        }

    if not experiment_name:
        raise ValueError("Provide --experiment_name or --run_id")

    experiment = client.get_experiment_by_name(experiment_name)
    if experiment is None:
        raise ValueError(f"Experiment '{experiment_name}' not found in MLflow at {uri}")

    order_by = (
        [f"metrics.{order_by_metric} DESC"] if order_by_metric else ["start_time DESC"]
    )
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=order_by,
        max_results=top_n,
    )

    return {
        "experiment": experiment_name,
        "experiment_id": experiment.experiment_id,
        "tracking_uri": uri,
        "total_returned": len(runs),
        "runs": [
            {
                "run_id": r.info.run_id,
                "status": r.info.status,
                "start_time": r.info.start_time,
                "metrics": dict(r.data.metrics),
                "params": dict(r.data.params),
            }
            for r in runs
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query MLflow for experiment runs, metrics, and parameters.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run run-mlflow-query.py --experiment_name my-usecase-training --top_n 5
  uv run run-mlflow-query.py --run_id abc123def456
  uv run run-mlflow-query.py --experiment_name my-usecase-training --order_by_metric test_r2 --top_n 10
""",
    )
    parser.add_argument(
        "--experiment_name",
        default=None,
        help="MLflow experiment name (e.g. my-usecase-training)",
    )
    parser.add_argument(
        "--run_id", default=None, help="Specific MLflow run ID to fetch"
    )
    parser.add_argument(
        "--order_by_metric", default=None, help="Metric name to sort by (descending)"
    )
    parser.add_argument(
        "--top_n", type=int, default=10, help="Number of runs to return (default: 10)"
    )
    parser.add_argument(
        "--tracking_uri",
        default=None,
        help="MLflow tracking URI (overrides MLFLOW_TRACKING_URI env var)",
    )
    args = parser.parse_args()

    try:
        result = query_runs(
            experiment_name=args.experiment_name,
            run_id=args.run_id,
            order_by_metric=args.order_by_metric,
            top_n=args.top_n,
            tracking_uri=args.tracking_uri,
        )
        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
