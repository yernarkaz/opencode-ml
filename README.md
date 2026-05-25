# opencode-ml — OpenCode Configuration Template for Azure ML Pipelines

A structured OpenCode configuration template providing specialised AI subagents,
slash commands, skills, and evaluation cases for Azure ML pipeline workflows —
from data preparation through to production deployment.

---

## What this repo is

A project-level OpenCode configuration template. It contains no application source
code — only agent definitions, skill files, slash commands, plugins, and backing
tool scripts that extend OpenCode for ML engineering workflows on Azure ML.

Drop this configuration into any Azure ML project repository and the agents
adapt to your use-case via `docs/data-schema.md` and `docs/experiment-conventions.md`.

---

## Directory structure

```
opencode-ml/
│
├── opencode.json               Project config — default_agent, permissions, MCP servers
├── AGENTS.md                   Rules for modifying this repo
│
├── docs/                       Context files — add your use-case schema and conventions here
│                               (loaded into every session via the instructions key)
│
├── .opencode/
│   ├── agents/                 Subagent definitions
│   │   ├── ml-orchestrator.md      Default entry point — routes all ML work
│   │   ├── ml-autoresearch.md      Autonomous improvement loop (steps: 200)
│   │   ├── ml-experiment-planner.md  Planning only, read-only, sequential-thinking MCP
│   │   ├── ml-code-builder.md      Write-capable pipeline code builder (edit+bash: allow)
│   │   ├── ml-code-reviewer.md     Read-only code review (edit+bash: deny)
│   │   └── ml-data-analyst.md      Read-only EDA and profiling (edit+bash: deny)
│   │
│   ├── commands/               Slash commands
│   │   ├── eda.md              /eda           — profile and audit a dataset
│   │   ├── train.md            /train         — run and track a training job
│   │   ├── evaluate.md         /evaluate      — compute metrics and check gates
│   │   ├── review-ml.md        /review-ml     — subtask code review
│   │   ├── deploy.md           /deploy        — promote model through D→Q→P
│   │   ├── monitor.md          /monitor       — check AML job status and metrics
│   │   ├── autoresearch.md     /autoresearch  — launch autonomous improvement loop
│   │   └── new-usecase.md      /new-usecase   — scaffold a new ML use-case
│   │
│   ├── plugins/                TypeScript hooks — run on every session start
│   │   ├── ml-env.ts           Injects PYTHONPATH=aml/pipeline/src
│   │   ├── ml-compaction.ts    Preserves ML state across context compaction
│   │   └── ml-tools.ts         Registers profile_dataset, run_mlflow_query, check_training
│   │
│   └── tools/                  Python backing scripts for registered tools (PEP 723)
│       ├── profile-dataset.py  Profiles parquet/CSV — shape, nulls, cardinality, skew
│       ├── run-mlflow-query.py Queries MLflow runs, metrics, and params
│       └── check-training.py   Polls AML job status and fetches logged metrics
│
└── .agents/
    └── skills/                 On-demand skill files (loaded explicitly, not auto-injected)
        │
        ├── ml-eda/
        │   ├── SKILL.md                  EDA workflow: profile_dataset, leakage audit, temporal checks
        │   ├── evals/evals.json          Eval test cases
        │   └── scripts/audit_leakage.py  CLI — audits offset_date leakage in feature files
        │
        ├── ml-data-cleansing/
        │   ├── SKILL.md                  Null handling, encoding, deduplication patterns
        │   ├── evals/evals.json          Eval test cases
        │   └── scripts/validate_data.py  CLI — validates cleaned datasets before feature engineering
        │
        ├── ml-experiment-tracking/
        │   ├── SKILL.md                  MLflow URI resolution, run lifecycle, model registry
        │   └── evals/evals.json          Eval test cases
        │
        ├── ml-model-development/
        │   ├── SKILL.md                  LightGBM/CatBoost/Optuna primary stack, temporal CV
        │   ├── evals/evals.json          Eval test cases
        │   └── references/
        │       ├── huggingface.md        HF fine-tuning reference (on-demand only)
        │       └── pyspark.md            PySpark ML reference (on-demand only)
        │
        ├── ml-evaluation/
        │   ├── SKILL.md                      Metric templates, calibration, D→Q gates
        │   ├── evals/evals.json              Eval test cases
        │   └── scripts/compute_metrics.py    CLI — computes metrics and checks acceptance gates
        │
        └── ml-deployment/
            ├── SKILL.md                  Online endpoint creation, D→Q→P promotion, idempotency rules
            └── evals/evals.json          Eval test cases
```

---

## Quick reference

### Starting a session

```bash
# From inside your ML source repo:
cd ~/your-ml-repo
opencode
```

The orchestrator (`ml-orchestrator`) is the default agent. Describe your task
in plain language — it routes to the appropriate subagent or skill.

### Common slash commands

| Command         | What it does                                                          |
| --------------- | --------------------------------------------------------------------- |
| `/eda`          | Profile a dataset and audit for leakage                               |
| `/train`        | Run a training job and log metrics                                    |
| `/evaluate`     | Compute metrics and check D→Q acceptance gates                        |
| `/review-ml`    | Code review in an isolated subtask context                            |
| `/deploy`       | Promote a model to D, Q, or P                                         |
| `/monitor`      | Check AML job status and fetch logged metrics                         |
| `/autoresearch` | Launch autonomous improvement loop (confirm mode first)               |
| `/new-usecase`  | Scaffold a new ML use-case (`/new-usecase <Repo> <problem> <metric>`) |

### Custom tools (available in all sessions via ml-tools.ts)

| Tool               | Script                      | Usage                               |
| ------------------ | --------------------------- | ----------------------------------- |
| `profile_dataset`  | `tools/profile-dataset.py`  | Shape, nulls, cardinality, skew     |
| `run_mlflow_query` | `tools/run-mlflow-query.py` | Query runs/metrics from MLflow      |
| `check_training`   | `tools/check-training.py`   | Poll AML job status + fetch metrics |

### Skill scripts (standalone CLI, not tool-registered)

| Script                                       | Usage                                                              |
| -------------------------------------------- | ------------------------------------------------------------------ |
| `ml-eda/scripts/audit_leakage.py`            | `python audit_leakage.py --file_path f.parquet`                                          |
| `ml-data-cleansing/scripts/validate_data.py` | `python validate_data.py --file_path f.parquet --required_cols col1,col2`                |
| `ml-evaluation/scripts/compute_metrics.py`   | `python compute_metrics.py --problem_type binary --pred_path p.parquet --target_col y`   |

### Agent roster

| Agent                   | Mode     | Edit | Purpose                                                       |
| ----------------------- | -------- | ---- | ------------------------------------------------------------- |
| `ml-orchestrator`       | primary  | no   | Entry point — routes work to the right subagent               |
| `ml-experiment-planner` | subagent | no   | Experiment design, architecture decisions, trade-off analysis |
| `ml-code-builder`       | subagent | yes  | Implements and fixes ML pipeline code; runs tests             |
| `ml-code-reviewer`      | subagent | no   | Reviews code for correctness, leakage, style, YAML sync       |
| `ml-data-analyst`       | subagent | no   | EDA, profiling, leakage audits                                |
| `ml-autoresearch`       | subagent | yes  | Autonomous modify-train-measure loop (Mode A/B)               |

Orchestrator routing: plan → `ml-experiment-planner` · implement/fix → `ml-code-builder` · review → `ml-code-reviewer` · EDA → `ml-data-analyst` · loop → `ml-autoresearch`

---

## Key constraints

- `share: disabled` — never change this
- `snapshot: false` — ML artefacts break snapshotting
- `PYTHONPATH=aml/pipeline/src` — injected by `ml-env.ts`; required for all pipeline scripts
- Do not add MCP servers here without checking the global config for duplicates
- Do not create Python source files or `requirements.txt` in this repo

---

## Autoresearch modes

The `/autoresearch` command launches `ml-autoresearch` and prompts for a mode:

- **Mode A (local)** — unlimited iterations on local compute, no AML cost
- **Mode B (AML)** — hard cap of 10 AML jobs per session; cherry-picks winning
  branch into main only; discards failing experiments

Add a `docs/program-<reponame>.md` file defining baseline metrics, open
hypotheses, and keep/discard rules for your use-case. Fill in baseline
metric values from MLflow before starting Mode B sessions.

---

## Adding a new ML use-case

```bash
/new-usecase MyRepoName regression r2
```

The command scaffolds:
- A new section in `docs/data-schema.md` (with `<FILL IN>` placeholders)
- `docs/program-<reponame>.md` — autoresearch template with baseline + hypotheses
- A printed onboarding checklist of what still needs to be done in the ADO repo

---

## MCP servers

| Server               | Type   | Purpose                              |
| -------------------- | ------ | ------------------------------------ |
| `sequential-thinking`| local  | Structured multi-step reasoning      |
| `context7`           | remote | Up-to-date library docs lookup       |

---

## References

### OpenCode

| Resource               | URL                               |
| ---------------------- | --------------------------------- |
| Docs home              | https://opencode.ai/docs          |
| Agents & subagents     | https://opencode.ai/docs/agents   |
| Slash commands         | https://opencode.ai/docs/commands |
| Plugins (hooks)        | https://opencode.ai/docs/plugins  |
| MCP servers            | https://opencode.ai/docs/mcp      |
| `opencode.json` schema | https://opencode.ai/docs/config   |

### Azure ML

| Resource                | URL                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------- |
| Python SDK v2 overview  | https://learn.microsoft.com/azure/machine-learning/concept-v2                                   |
| `MLClient` reference    | https://learn.microsoft.com/python/api/azure-ai-ml/azure.ai.ml.mlclient                         |
| Online endpoints        | https://learn.microsoft.com/azure/machine-learning/concept-endpoints-online                     |
| AML pipeline components | https://learn.microsoft.com/azure/machine-learning/concept-component                            |
| Managed Identity auth   | https://learn.microsoft.com/azure/machine-learning/how-to-identity-based-service-authentication |

### MLflow

| Resource                     | URL                                                                           |
| ---------------------------- | ----------------------------------------------------------------------------- |
| Tracking API                 | https://mlflow.org/docs/latest/tracking.html                                  |
| `azureml-mlflow` integration | https://learn.microsoft.com/azure/machine-learning/how-to-use-mlflow-cli-runs |
| Model registry               | https://mlflow.org/docs/latest/model-registry.html                            |
| `MlflowClient` reference     | https://mlflow.org/docs/latest/python_api/mlflow.client.html                  |

### ML stack

| Resource                            | URL                                                                                             |
| ----------------------------------- | ----------------------------------------------------------------------------------------------- |
| LightGBM Python API                 | https://lightgbm.readthedocs.io/en/latest/pythonapi/lightgbm.LGBMClassifier.html                |
| CatBoost Python API                 | https://catboost.ai/docs/concepts/python-reference_catboostclassifier                           |
| Optuna quickstart                   | https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/001_first.html                 |
| scikit-learn `MultiOutputRegressor` | https://scikit-learn.org/stable/modules/generated/sklearn.multioutput.MultiOutputRegressor.html |

### Skills & agent standards

| Resource                           | URL                                                                                              |
| ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| agentskills.io — skill file spec   | https://agentskills.io/home                                                                      |
| agentskills.io — `SKILL.md` format | https://agentskills.io/skill-creation/best-practices                                             |
| sequential-thinking MCP            | https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking                 |
