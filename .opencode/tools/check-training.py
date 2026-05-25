"""Check the status of an Azure ML training job and retrieve logged metrics.

PEP 723 inline dependencies — run with: uv run check-training.py --job_name <name> ...
Requires az CLI to be authenticated (az login or Managed Identity in AML compute).
"""

# /// script
# dependencies = [
#   "azure-ai-ml>=1.13",
#   "azure-identity>=1.15",
# ]
# ///

import argparse
import json
import sys
import logging

logger = logging.getLogger(__name__)

# Terminal job statuses — no point polling further
TERMINAL_STATUSES = {"Completed", "Failed", "Canceled", "NotResponding"}


def check_job(job_name: str, workspace_name: str, resource_group: str) -> dict:
    from azure.identity import DefaultAzureCredential
    from azure.ai.ml import MLClient

    credential = DefaultAzureCredential()
    ml_client = MLClient(
        credential=credential,
        subscription_id=None,  # resolved from workspace
        resource_group_name=resource_group,
        workspace_name=workspace_name,
    )

    job = ml_client.jobs.get(job_name)

    result: dict = {
        "job_name": job_name,
        "status": job.status,
        "terminal": job.status in TERMINAL_STATUSES,
        "display_name": getattr(job, "display_name", job_name),
        "creation_time": str(
            getattr(getattr(job, "creation_context", None), "created_at", "")
        ),
        "studio_url": getattr(job, "studio_url", None),
    }

    # Retrieve metrics from MLflow if the job is complete
    if job.status == "Completed":
        try:
            mlflow_uri = ml_client.workspaces.get(workspace_name).mlflow_tracking_uri
            import mlflow
            from mlflow.tracking import MlflowClient

            mlflow.set_tracking_uri(mlflow_uri)
            client = MlflowClient()

            # AML jobs use the job name as the MLflow run name
            runs = client.search_runs(
                experiment_ids=[],
                filter_string=f"tags.mlflow.rootRunId = '{job_name}' OR attributes.run_name = '{job_name}'",
                max_results=1,
            )
            if runs:
                run = runs[0]
                result["metrics"] = dict(run.data.metrics)
                result["params"] = dict(run.data.params)
                result["mlflow_run_id"] = run.info.run_id
            else:
                result["metrics"] = {}
                result["mlflow_warning"] = "No MLflow run found matching job name"
        except Exception as e:
            result["metrics"] = {}
            result["mlflow_warning"] = f"Could not retrieve MLflow metrics: {e}"
    else:
        result["metrics"] = {}

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check Azure ML job status and retrieve metrics when complete.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run check-training.py --job_name my-training-job-abc123 --workspace_name ws-dev --resource_group my-resource-group
  uv run check-training.py --job_name my-training-job-xyz --workspace_name ws-qa --resource_group my-resource-group

Exit codes:
  0  Job found and status returned successfully
  1  Error fetching job (authentication failure, job not found, etc.)
""",
    )
    parser.add_argument("--job_name", required=True, help="Azure ML job name")
    parser.add_argument(
        "--workspace_name", required=True, help="Azure ML workspace name"
    )
    parser.add_argument(
        "--resource_group", required=True, help="Azure resource group name"
    )
    args = parser.parse_args()

    try:
        result = check_job(
            job_name=args.job_name,
            workspace_name=args.workspace_name,
            resource_group=args.resource_group,
        )
        print(json.dumps(result, indent=2, default=str))

        # Non-zero exit if job failed — lets autoresearch agent detect failures
        if result["status"] == "Failed":
            sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e), "job_name": args.job_name}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
