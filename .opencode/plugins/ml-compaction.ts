import type { Plugin } from "@opencode-ai/plugin"

/**
 * ml-compaction.ts — ML session compaction plugin
 *
 * Injects ML-specific state into the compaction prompt so that critical
 * context (active repo, pipeline stage, last metric, open hypotheses)
 * survives context window compaction.
 *
 * Runs on every session compaction — keep this fast and side-effect-free.
 */
export const MLCompactionPlugin: Plugin = async ({ $, directory }) => {
  return {
    "experimental.session.compacting": async (_input, output) => {
      // Gather live state at compaction time
      let branch = "unknown"
      let programBaseline = "not set"
      let openHypotheses = "none"

      try {
        const branchResult = await $`git -C ${directory} branch --show-current`.quiet()
        branch = branchResult.stdout.toString().trim()
      } catch {
        // not a git repo or git not available — safe to ignore
      }

      try {
        const baselineResult =
          await $`grep -A1 "## Baseline" ${directory}/program.md`.quiet()
        const lines = baselineResult.stdout.toString().trim().split("\n")
        programBaseline = lines[1]?.trim() ?? "not set"
      } catch {
        // program.md not present in this repo
      }

      try {
        const hypothesesResult =
          await $`grep -A20 "## Open hypotheses" ${directory}/program.md`.quiet()
        const numbered = hypothesesResult.stdout
          .toString()
          .split("\n")
          .filter((l: string) => /^\d+\./.test(l.trim()))
          .slice(0, 5)
          .join(", ")
        openHypotheses = numbered || "none"
      } catch {
        // program.md not present
      }

      output.context.push(`## ML Session State (preserve across compaction)

- **Repo directory**: ${directory}
- **Git branch**: ${branch}
- **Active program.md baseline**: ${programBaseline}
- **Open hypotheses (top 5)**: ${openHypotheses}
- **Pipeline**: preprocess_clean_data → engineer_features → train_model → inference_model
- **Deployment gates**: D → Q → P (never skip)
- **Primary stack**: LightGBM / CatBoost / Optuna
- **PYTHONPATH**: aml/pipeline/src (injected by ml-env plugin)
- **Boolean CLI flags**: str_to_bool only — never store_true/store_false
- **MLflow URI**: fetch from ml_client.workspaces.get(workspace).mlflow_tracking_uri`)
    },
  }
}
