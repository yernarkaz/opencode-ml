import type { Plugin } from "@opencode-ai/plugin"
import { tool } from "@opencode-ai/plugin"
import * as path from "path"

/**
 * ml-tools.ts — Custom ML tools plugin
 *
 * Registers three tools available to all agents in this session:
 *   - profile_dataset   : profile a parquet/CSV file and return structured stats
 *   - run_mlflow_query  : query MLflow for runs, metrics, and parameters
 *   - check_training    : poll an Azure ML job for status and retrieve metrics
 *
 * Each tool delegates to a Python backing script in .opencode/tools/
 * via `uv run` so dependencies are fully isolated (PEP 723).
 */
export const MLToolsPlugin: Plugin = async ({ $, directory }) => {
  const toolsDir = path.join(directory, ".opencode", "tools")

  return {
    tool: {
      profile_dataset: tool({
        description:
          "Profile a parquet or CSV dataset and return shape, dtypes, null rates, cardinality, numeric stats, and target distribution. Use before writing any analysis code. Accepts a file path argument.",
        args: {
          file_path: tool.schema.string(),
          target_col: tool.schema.string().optional(),
          sample_rows: tool.schema.number().optional(),
        },
        async execute(args) {
          const script = path.join(toolsDir, "profile-dataset.py")
          const cmdArgs = [`--file_path`, args.file_path]
          if (args.target_col) cmdArgs.push("--target_col", args.target_col)
          if (args.sample_rows)
            cmdArgs.push("--sample_rows", String(args.sample_rows))

          const result = await $`uv run ${script} ${cmdArgs}`.quiet()
          return result.stdout.toString()
        },
      }),

      run_mlflow_query: tool({
        description:
          "Query MLflow for experiment runs, logged metrics, and parameters. Supports fetching a specific run by ID or listing the top N runs by a metric. Returns JSON. Requires the MLflow tracking URI to be set in the environment.",
        args: {
          experiment_name: tool.schema.string().optional(),
          run_id: tool.schema.string().optional(),
          order_by_metric: tool.schema.string().optional(),
          top_n: tool.schema.number().optional(),
        },
        async execute(args) {
          const script = path.join(toolsDir, "run-mlflow-query.py")
          const cmdArgs: string[] = []
          if (args.experiment_name)
            cmdArgs.push("--experiment_name", args.experiment_name)
          if (args.run_id) cmdArgs.push("--run_id", args.run_id)
          if (args.order_by_metric)
            cmdArgs.push("--order_by_metric", args.order_by_metric)
          if (args.top_n) cmdArgs.push("--top_n", String(args.top_n))

          const result = await $`uv run ${script} ${cmdArgs}`.quiet()
          return result.stdout.toString()
        },
      }),

      check_training: tool({
        description:
          "Check the status of an Azure ML training job and retrieve its logged metrics when complete. Returns JSON with job status, duration, and metrics. Requires az CLI to be logged in.",
        args: {
          job_name: tool.schema.string(),
          workspace_name: tool.schema.string(),
          resource_group: tool.schema.string(),
        },
        async execute(args) {
          const script = path.join(toolsDir, "check-training.py")
          const result =
            await $`uv run ${script} --job_name ${args.job_name} --workspace_name ${args.workspace_name} --resource_group ${args.resource_group}`.quiet()
          return result.stdout.toString()
        },
      }),
    },
  }
}
