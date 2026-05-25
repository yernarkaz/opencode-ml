import type { Plugin } from "@opencode-ai/plugin"

/**
 * ml-env.ts — ML environment plugin
 *
 * Injects PYTHONPATH into every shell execution so that pipeline scripts
 * resolve internal imports from aml/pipeline/src without manual setup.
 *
 * Runs on every OpenCode session — keep this fast and side-effect-free.
 */
export const MLEnvPlugin: Plugin = async ({ directory }) => {
  return {
    "shell.env": async (_input, output) => {
      const existing = output.env.PYTHONPATH ?? ""
      const srcPath = `${directory}/aml/pipeline/src`

      // Prepend only if not already present to avoid duplicate entries
      if (!existing.includes(srcPath)) {
        output.env.PYTHONPATH = existing ? `${srcPath}:${existing}` : srcPath
      }
    },
  }
}
