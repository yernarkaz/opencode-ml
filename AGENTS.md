# AGENTS.md — Opencode-ML-AI Configuration Repo

This file governs agent behaviour when working **inside this repository only**.
This repo contains OpenCode configuration files for ML engineering workflows.
It is not a source code repo — do not treat it as one.

---

## What this repo contains

```
opencode.json               project-level OpenCode config
AGENTS.md                   this file
docs/                       always-loaded domain context (via instructions key)
.opencode/agents/           subagent definitions
.opencode/commands/         slash command definitions
.opencode/plugins/          TypeScript plugin hooks
.opencode/tools/            custom tool definitions + Python backing scripts
.agents/skills/             on-demand skill files (loaded explicitly by agent)
```

---

## Rules for modifying this repo

### opencode.json
- Never change `"share"` from `"disabled"`.
- Never remove `"snapshot": false` — ML artefacts (*.pt, *.ckpt) break snapshotting.
- Permission rules use last-match-wins: the wildcard `"*": "allow"` must stay first; specific overrides follow it.
- Do not add MCP servers here without confirming they are not already registered in the global config (`~/.config/opencode/opencode.json`). Duplicates cause conflicts.

### Skills (`.agents/skills/*/SKILL.md`)
- Each skill lives in its own subdirectory: `.agents/skills/<name>/SKILL.md`.
- Skills are on-demand — they are loaded explicitly by the agent, not injected automatically.
- Keep skills focused on a single ML stage. Do not merge two stages into one skill.

### Subagents (`.opencode/agents/*.md`)
- Subagents that only read (data analyst, code reviewer) must have `edit: deny` and `bash: deny` in their tool restrictions.
- Never give a subagent broader permissions than the parent session.

### Commands (`.opencode/commands/*.md`)
- Commands use `!``shell command` `` syntax to inject live shell output into the prompt.
- The `/review-ml` command uses `subtask: true` — do not remove this; it isolates review context from the main session.
- After any change to AML component YAML files or `ArgumentParser` definitions in the target repos, the `/train` command reminder to run component validation must be preserved.

### Plugins (`.opencode/plugins/*.ts`)
- `ml-env.ts` injects `PYTHONPATH=aml/pipeline/src`. Update this only if the repo structure changes.
- Plugins run on every session — keep them fast and side-effect-free.

### docs/ files
- Files placed in `docs/` and listed under the `instructions` key in `opencode.json` are loaded into every session. Keep them concise — they consume context on every message.
- Domain vocabulary (column names, experiment names, model naming format) belongs in `docs/`, not in AGENTS.md.

---

## What NOT to do in this repo

- Do not create Python source code files here (this is a config repo).
- Do not create a `requirements.txt` or `pyproject.toml` here.
- Do not commit `.env` files or any file containing credentials.
- Do not modify `~/.config/opencode/opencode.json` (global config) from here.
- Do not duplicate skill content that already exists in the global `~/.agents/skills/` installation.
