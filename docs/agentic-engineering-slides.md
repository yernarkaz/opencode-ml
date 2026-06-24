# Agentic Engineering with OpenCode for Machine Learning (ML) Use Cases

Visual layouts, diagrams, and blueprints for a hands-on talk on building a purpose-built agentic SDLC for ML engineering. Grounded in a real OpenCode configuration: **6 subagents · 13 skills · 9 slash commands · Azure ML**. Conceptual framing is kept broad — the patterns apply equally to software, QA, and BA teams.

---

## Slide 1: What is Agentic Engineering & How We Got Here

### Visual Layout: Split Origin Story + Sandbox Flow

- **Structure:** Top half — a 3-stage origin timeline showing the team's journey. Bottom half — the universal sandbox flow showing what the end state looks like.
- **Color Palette:** Warm Gray (journey) → Cold Gray/Amber/Green (sandbox flow).

### Diagram

```text
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  "It started as just add an AI assistant to our ML pipelines..."            │
  └─────────────────────────────────────────────────────────────────────────────┘

  [ STAGE 1 ]                [ STAGE 2 ]                   [ STAGE 3 ]
  AI as a Copilot            AI runs tasks —                Purpose-built
                             things go wrong                Agentic SDLC
  ─────────────────          ──────────────────             ─────────────────────
  Chat assistant.            Agent modifies files           ml-orchestrator routes
  Writes some code.          it shouldn't.                  to 6 locked specialists.
  Manual execution.          No guardrails.                 13 skills. 9 commands.
                             No audit trail.                Minimum permissions.

────────────────────────────────────────────────────────────────────────────────

  MANUAL INPUT                ORCHESTRATED EXECUTION              VERIFIED OUTPUT
 ┌──────────────────┐        ┌───────────────────────────┐       ┌──────────────┐
 │ Ad-hoc commands  │ ─────► │  ml-orchestrator          │ ────► │ Consistent   │
 │ Human errors     │        │  routes to 6 specialists  │       │ Auditable    │
 │ No audit trail   │        │  under enforced guardrails│       │ Repeatable   │
 └──────────────────┘        └───────────────────────────┘       └──────────────┘
```

### Slide Content

- **Software 3.0 (Karpathy):** Hand-coded logic (1.0) → learned neural networks (2.0) → programming in plain English where LLMs are the runtime (3.0). Agentic Engineering is what Software 3.0 looks like in production: not one model you prompt, but a governed team of specialists you orchestrate.
- **Definition:** Autonomous, role-specialized agents execute engineering workflows under enforced guardrails — replacing unreliable manual processes with consistent, auditable automation.
- **Karpathy's principles — encoded, not suggested:** Think before coding · Prefer simplicity · Surgical changes · Goal-driven. These are hardcoded into `ml-experiment-planner` and enforced before any implementation begins.

---

## Slide 2: Value Proposition

### Visual Layout: 2×2 Card Grid

- **Structure:** 4 benefit cards in a 2×2 grid with bold titles and concrete ML examples.
- **Color Palette:** Charcoal Blue headers, Light Slate fills.

### Diagram

```text
┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│ SPEED                             │   │  QUALITY                          │
│                                   │   │                                   │
│ /eda, /train, /deploy remove      │   │ Temporal leakage guards,          │
│ manual orchestration overhead     │   │ str_to_bool enforcement, and      │
│ and cut ML feedback loops         │   │ component YAML sync are checked   │
│ from hours to minutes.            │   │ automatically — before every PR.  │
└───────────────────────────────────┘   └───────────────────────────────────┘

┌───────────────────────────────────┐   ┌───────────────────────────────────┐
│ CONSISTENCY                       │   │ TRANSPARENCY                      │
│                                   │   │                                   │
│ Every ML workflow follows the     │   │ Every agent action is logged.     │
│ same steps regardless of who      │   │ Decisions, tool calls, and        │
│ ran it — same guardrails,         │   │ outputs form a complete,          │
│ same review, same gates.          │   │ readable audit trail.             │
└───────────────────────────────────┘   └───────────────────────────────────┘
```

---

## Slide 3: Core Concepts Demystified

### Visual Layout: Glossary Table with Analogy and OpenCode Columns

- **Structure:** Term, definition, real-world analogy, and the actual OpenCode equivalent — side by side.
- **Color Palette:** Navy (Term) → Teal (Analogy) → Slate (OpenCode).

### Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────────┐
│  TERM           DEFINITION                       ANALOGY           OPENCODE        │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Agent          Autonomous specialist with a     Contractor with   ml-code-builder │
│                 defined role and tool access.    a scoped remit.   ml-data-analyst  │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Orchestrator   The main agent that routes       Project manager   ml-orchestrator  │
│                 tasks to the right specialists.  assigning work.   (primary agent)  │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Skill          Domain-specific rulebook         Specialist's      ml-eda           │
│                 loaded by an agent on demand.    job manual.       ml-deployment    │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Guardrail      Enforced constraint that         Building code     "az ml *": "ask" │
│                 blocks dangerous actions.        no one bypasses.  edit: deny       │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Command        Trigger that initiates a         Work order that   /eda  /train     │
│                 multi-agent workflow.            kicks off team.   /deploy          │
├────────────────────────────────────────────────────────────────────────────────────┤
│  Plugin         Session-scoped hook that         Shared toolbox    ml-env.ts        │
│                 injects context or tools.        on every desk.    ml-tools.ts      │
└────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Slide 4: The Execution Lifecycle

### Visual Layout: Milestone Timeline with Governance Gate Banner

- **Structure:** 7 numbered milestones on a horizontal path. Actual slash commands shown below each phase. Governance gates called out.
- **Color Palette:** Warm Gray path, Slate nodes, Alert Red gate.

### Diagram

```text
  ( 01 ) ─── ( 02 ) ─── ( 03 ) ─── ( 04 ) ─── ( 05 ) ─── ( 06 ) ─── ( 07 )
   Plan       Analyze    Build      Test        Review      Deploy     Monitor

   Design     Profile    Write      Run unit    Flag        Promote    Observe
   experiment data,      pipeline   tests &     leakage,    D → Q →    endpoint
   & features leakage,   code &     validate    style, &    P gates    drift &
              quality    configs    YAMLs       patterns               metrics

  /new-usecase  /eda     /train    /train      /review-ml  /deploy    /monitor


┌──────────────────────────────────────────────────────────────────────────────┐
│   GOVERNANCE GATES: Phase 01 (Plan) and Phase 05 (Review) must pass        │
│     before any deployment or environment promotion is permitted.             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Slide Content

- **Same lifecycle, different artifacts:** ML teams produce experiment plans and pipeline code; software teams ship features; QA teams produce test suites — the 7-phase flow is identical across all roles.

---

## Slide 5: Architecture & How it Works

### Visual Layout: Layered Stack + Request Trace

- **Structure:** Top section shows the full 5-layer architecture with actual agent names and counts. Bottom section traces one real command (/eda) through the system.
- **Color Palette:** Slate Blue (Control) → Teal (Integration).

### Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — 9 SLASH COMMANDS                                                    │
│  /eda  /train  /evaluate  /review-ml  /deploy  /monitor  /autoresearch         │
│  /new-usecase  /cleanup                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 2 — ml-orchestrator  (Haiku 4.5 · read-only · routes + governs)         │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — 5 SPECIALIST SUBAGENTS                                              │
│  ml-experiment-planner (Opus 4.8 · read)  ml-data-analyst (Haiku 4.5 · read)  │
│  ml-code-builder (Sonnet 4.6 · write)     ml-code-reviewer (Haiku 4.5 · read) │
│  ml-autoresearch (Sonnet 4.6 · write · autonomous loop)                        │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4 — 13 SKILLS · 3 PLUGINS · 3 TOOLS                                    │
│  ml-eda · ml-deployment · ml-model-development · ml-evaluation · +9 more       │
│  ml-env.ts · ml-tools.ts · ml-compaction.ts                                    │
│  profile-dataset.py · run-mlflow-query.py · check-training.py                  │
├────────────────────────────────────────────────────────────────────────────────┤
│  LAYER 5 — Azure ML CLI v2 · MLflow · Online Endpoints · D → Q → P            │
└────────────────────────────────────────────────────────────────────────────────┘

  REQUEST TRACE  /eda data/features.parquet
  ──────────────────────────────────────────────────────────────────────────────
  ml-orchestrator  →  ml-data-analyst  →  loads ml-eda skill  →  runs
  sees "explore"      read-only           leakage rules,          profile-dataset.py
  keyword             edit: deny          null checks,            on parquet
                      bash: deny          offset_date audit   →   structured report
                                                              →   full action log
```

---

## Slide 6: Guardrails & Safety — How the Config Actually Works

### Visual Layout: Two-Layer Config Breakdown

- **Structure:** Two side-by-side config panels showing the actual syntax. Left: `opencode.json` global bash intercepts. Right: agent frontmatter per-agent permissions. Below: what this combination produces in practice.
- **Color Palette:** Alert Crimson (Banner) → Slate (Config) → Teal (Effect).

### Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│   Two-layer permission model — global config + per-agent frontmatter         │
└────────────────────────────────────────────────────────────────────────────────┘

  LAYER 1 — opencode.json                  LAYER 2 — agent frontmatter (.md)
  ─────────────────────────────────────    ─────────────────────────────────────
  "permission": {                          # ml-code-reviewer (read-only)
    "bash": {                              permission:
      "*":             "allow",  ◄──────     edit: deny
      "rm *":          "ask",               bash: deny
      "git push *":    "ask",
      "git reset *":   "ask",              # ml-experiment-planner (read-only)
      "pip install *": "ask",              permission:
      "conda install *":"ask",               edit: deny
      "poetry add *":  "ask",
      "az ml *":       "ask"  ◄── all AML  # ml-code-builder (write-capable)
    },                                     permission:
    "external_directory": {                  edit: allow
      "~/datasets/**": "allow",              bash: allow
      "/data/**":      "allow"
    }                                      # ml-orchestrator (governance only)
  }                                        permission:
                                             edit: deny
  Last-match-wins: wildcard "allow"          task:
  first, specific "ask" overrides it.          "*": deny
                                               "ml-code-builder": allow
                                               "ml-data-analyst": allow

  WHAT THIS PRODUCES IN PRACTICE
  ─────────────────────────────────────────────────────────────────────────────
  Agent tries...                           Result
  ───────────────────────────────────────  ───────────────────────────────────
  ml-data-analyst runs python script       ✔ Allowed (bash: allow at global level,
                                             but edit: deny means no file writes)
  ml-code-reviewer edits a file            ✗ Blocked — edit: deny in frontmatter
  any agent runs: az ml job create         ⚠ Intercepted — human must confirm
  any agent runs: git push origin main     ⚠ Intercepted — human must confirm
  ml-orchestrator spawns unknown agent     ✗ Blocked — task: "*": deny
```

### Slide Content

- **Why `"*": "allow"` first?** Last-match-wins means the wildcard is the default; specific `"ask"` rules after it selectively intercept only the commands that matter. Simpler than allowlisting everything.
- **Skills as a third layer:** Coding patterns (`str_to_bool`, no hardcoded URIs, `< offset_date` leakage guard) are enforced in skill files — not the permission system. Skills encode *what correct looks like*; permissions encode *what is allowed to run*. Both must hold.

---

## Slide 7: The 4 Core Workflows — Commands · Agents · Skills

### Visual Layout: 2×2 ML Workflow Quadrant Grid + Cross-Role Footer

- **Structure:** Each quadrant maps a daily ML workflow to its command, agent, skill, and deliverable. Footer note shows the pattern generalizes to other engineering roles.
- **Color Palette:** Deep Blue · Indigo · Teal · Forest Green.

### Diagram

```text
┌─────────────────────────────────────────┬─────────────────────────────────────────┐
│  EDA & DATA PROFILING                   │  EXPERIMENT PLANNING                    │
│  /eda <path>                            │  /new-usecase, /train                   │
│                                         │                                         │
│  ml-data-analyst  (read-only)           │  ml-experiment-planner  (read-only)     │
│    └─ Skill: ml-eda                     │    └─ Skill: ml-model-development        │
│    └─ Tool:  profile-dataset.py         │    └─ MCP:   sequential-thinking         │
│                                         │                                         │
│  → Dataset profile (nulls, dtypes)      │  → Structured experiment plan           │
│  → Leakage risk flags                   │  → Hypothesis & acceptance criteria      │
│  → Target distribution report           │  → Feature strategy & sequenced steps   │
├─────────────────────────────────────────┼─────────────────────────────────────────┤
│  CODE BUILD & REVIEW                    │  DEPLOY & MONITOR                       │
│  /train, /review-ml                     │  /deploy, /monitor, /autoresearch        │
│                                         │                                         │
│  ml-code-builder   (write)              │  ml-code-builder   (scoped CLI)         │
│    └─ Skill: ml-model-development       │    └─ Skill: ml-deployment              │
│    └─ Skill: feature-engineering-toolkit│  ml-autoresearch   (autonomous loop)    │
│  ml-code-reviewer  (read-only)          │    └─ Skill: ml-monitoring              │
│    └─ Skill: ml-evaluation              │    └─ Tool:  run-mlflow-query.py        │
│                                         │    └─ Tool:  check-training.py          │
│  → Validated pipeline diffs             │                                         │
│  → Unit tests passing                   │  → Promoted endpoint Dev → QA → Prod   │
│  → CRITICAL/WARNING review              │  → Drift & performance monitoring       │
│  → Component YAML sync confirmed        │  → autoresearch results.tsv log         │
└─────────────────────────────────────────┴─────────────────────────────────────────┘

  Same 4-quadrant pattern applies across roles — only agents, skills, and tooling differ:
  SWE: design/build/review/deploy  ·  QA: plan/write/run/triage  ·  BA: profile/validate/document/publish
```

---

## Slide 8: Role Applicability — The Same Pattern Across Teams

### Visual Layout: Cross-Role Comparison Table

- **Structure:** Full-width table with ML as the primary highlighted row, followed by three other engineering roles — showing the common orchestration foundation beneath all of them.
- **Color Palette:** Slate header, ML row highlighted, alternating light fills.

### Diagram

```text
┌──────────────────┬──────────────────────────────┬────────────────────────┬─────────────────────────────┐
│  ROLE            │  CORE AGENTS                 │  KEY SKILLS            │  PRIMARY DELIVERABLE        │
├──────────────────┼──────────────────────────────┼────────────────────────┼─────────────────────────────┤
│  ML Engineer ★   │  orchestrator · planner ·    │  ml-eda · model-dev ·  │  Validated pipeline +       │
│  (this talk)     │  analyst · builder ·         │  evaluation · deploy · │  promoted Azure ML          │
│                  │  reviewer · autoresearch      │  monitoring (13 total) │  endpoint + metrics log     │
├──────────────────┼──────────────────────────────┼────────────────────────┼─────────────────────────────┤
│  Software Eng.   │  Architect · Builder ·       │  Design · Standards ·  │  Reviewed, tested feature   │
│                  │  Test-Gen · Deployer          │  Coverage · CI/CD      │  merged to main             │
├──────────────────┼──────────────────────────────┼────────────────────────┼─────────────────────────────┤
│  Business Analyst│  Data Analyst ·              │  Profiling · Req.      │  Stakeholder report +       │
│                  │  Req-Validator · Writer       │  Validation · Docs     │  structured requirements    │
├──────────────────┼──────────────────────────────┼────────────────────────┼─────────────────────────────┤
│  QA Engineer     │  Test-Planner · Writer ·     │  Edge Cases · Baseline │  Test suite + regression    │
│                  │  Regression · Triager         │  · Defect Classification│  report + severity list    │
└──────────────────┴──────────────────────────────┴────────────────────────┴─────────────────────────────┘

  Common foundation across all roles: Orchestrator · Guardrails · Scoped Permissions · Audit Trail
```

### Slide Content

- The domain changes — the architecture does not. Any team can adopt the same orchestration layer, swap in role-specific agents and skills, and inherit all guardrails and audit trail behavior for free.

---

## Slide 9: What You Get — Concrete ML Deliverables

### Visual Layout: Full Pipeline Delivery Table

- **Structure:** End-to-end table mapping each ML stage to its command, executing agent, guardrail that fires, and the specific artifact produced — including its actual content format.
- **Color Palette:** Slate header · Cool Blue (agent) · Amber (guardrail) · Forest Green (artifact).

### Diagram

```text
┌──────────┬──────────────┬──────────────────────┬────────────────────────┬──────────────────────────────────────┐
│  STAGE   │  COMMAND     │  AGENT               │  GUARDRAIL FIRES       │  ARTIFACT & FORMAT                   │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  EDA     │  /eda        │  ml-data-analyst     │  offset_date leakage   │   dataset-profile.md               │
│          │              │  (edit: deny)        │  audit on every column │  Shape · nulls · skew · cardinality  │
│          │              │                      │                        │  Leakage risk flags · top-5 values   │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  Plan    │  /train      │  ml-experiment-      │  Plan required before  │   experiment-plan.md               │
│          │  (step 1)    │  planner             │  any code is written   │  Objective · Approach · Risks        │
│          │              │  (edit: deny)        │  Karpathy: think first │  Steps · Success criteria            │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  Build   │  /train      │  ml-code-builder     │  str_to_bool enforced  │   pipeline diffs (ruff-validated)  │
│          │  (step 2)    │  (edit: allow)       │  No hardcoded URIs     │  Unit tests: pytest tests/unit/      │
│          │              │                      │  ManagedIdentity only  │  YAML sync: component args matched   │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  Review  │  /review-ml  │  ml-code-reviewer    │  CRITICAL blocks       │   structured findings              │
│          │              │  (edit: deny,        │  deploy until resolved │  [CRITICAL] file:line — issue — fix  │
│          │              │   bash: deny)        │  Isolated subtask      │  [WARNING]  file:line — issue — fix  │
│          │              │                      │                        │  Summary: pass / needs changes       │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  Deploy  │  /deploy     │  ml-code-builder     │  "az ml *": "ask"      │   active online endpoint           │
│          │              │  (scoped CLI)        │  D→Q→P order enforced  │  Dev → QA → Prod promotion log       │
│          │              │                      │  Human confirm each    │  Smoke-test payload result           │
├──────────┼──────────────┼──────────────────────┼────────────────────────┼──────────────────────────────────────┤
│  Monitor │  /monitor    │  ml-autoresearch     │  Drift threshold alert │   monitoring schedule (Azure ML)   │
│          │  /autoresearch│ (edit: allow,       │  10 AML job cap        │  results.tsv per iteration:          │
│          │              │   autonomous loop)   │  Cherry-pick only —    │  hypothesis · Δmetric · KEPT/DISCARD │
│          │              │                      │  no direct merge       │  Best result surfaced for promotion  │
└──────────┴──────────────┴──────────────────────┴────────────────────────┴──────────────────────────────────────┘
```

### Slide Content

- **Nothing is implicit:** Every artifact has a known producer (agent), a known validator (guardrail), and a known format. The orchestrator enforces the sequence — no stage is reached without the previous one completing.
- **The autoresearch loop is unique to agentic systems:** An agent runs modify → train → measure → keep/discard cycles overnight, logs every iteration to `results.tsv`, and surfaces only the best commit for human review. No human in the loop until a result is ready to promote.

---

## Slide 10: Anti-Patterns to Avoid

### Visual Layout: Warning Banner with Numbered Anti-Pattern List

- **Structure:** Red warning header, 5 anti-patterns grounded in real ML and agentic engineering failures, each with a one-line remedy.
- **Color Palette:** Alert Crimson (Header) → Amber (Anti-pattern) → Green (Remedy).

### Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│  ⚠  Mistakes that eliminate the safety and reproducibility benefits            │
└────────────────────────────────────────────────────────────────────────────────┘

  ✗  1. OVER-PERMISSIONING
        Giving all agents edit: allow defeats the scoped-permissions model entirely.
        ✓  Default is read-only. Write access is granted per-agent, not globally.

  ✗  2. MEGA-SKILLS
        One 500-line skill covering EDA, training, and deployment becomes unmaintainable.
        ✓  One skill per ML stage (ml-eda, ml-deployment…). Each independently updatable.

  ✗  3. SKIPPING THE REVIEW GATE
        Running /deploy without a prior /review-ml to save time.
        ✓  ml-orchestrator enforces: plan → build → review → deploy. Non-negotiable.

  ✗  4. HARDCODING ENVIRONMENT DETAILS IN SKILLS
        Skills that reference specific workspace names, storage URIs, or cluster names.
        ✓  Skills reference docs/ schema files only. Environment values come from config.

  ✗  5. SKILL DRIFT
        Skills describe the pipeline as it was months ago. Agents follow stale rules.
        ✓  Treat skills as living documents. Update alongside ArgumentParser changes.
```

---

## Slide 11: Adoption Path & Summary

### Visual Layout: Maturity Staircase + 3-Step Setup + Strengths/Next Steps

- **Structure:** Three sections stacked — maturity levels (where are you now), getting started (how to move), and strengths/next steps panels.
- **Color Palette:** Light Gray → Deep Green (maturity) · Slate/Teal/Green (steps) · Blue-Green/Amber (summary).

### Diagram

```text
  MATURITY MODEL
  ──────────────────────────────────────────────────────────────────────────────
  L0 Manual      All commands by hand. No agents.        az ml job create by hand
  L1 Assisted    Slash commands, one generalist agent.   /train exists but unscoped
  L2 Orchestrated  Multi-agent routing via orchestrator. ml-orchestrator + 5 agents
  L3 Governed    Guardrails, D→Q→P gates, audit trails.  opencode.json intercepts ★
  L4 Adaptive    Autonomous experiment loops + metrics.  /autoresearch + results.tsv

  This setup operates at L3–L4.  Recommended target for production use: L3.
  ──────────────────────────────────────────────────────────────────────────────

  GETTING STARTED IN 3 STEPS
  ┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────────────────┐
  │  STEP 1  ~ 30 min        │  │  STEP 2  ~ 2 hours       │  │  STEP 3  Immediate       │
  │  Drop in opencode.json   │  │  Define agents & skills  │  │  Run /eda or /review-ml  │
  │  + docs/ folder. Zero    │  │  One .md per agent.      │  │  Observe routing, skill  │
  │  source code changes.    │  │  edit: deny by default.  │  │  load, and audit trail.  │
  └──────────────────────────┘  └──────────────────────────┘  └──────────────────────────┘
  ──────────────────────────────────────────────────────────────────────────────

  ┌─────────────────────────────────────────┐  ┌─────────────────────────────────────────┐
  │   STRENGTHS                           │  │   NEXT STEPS                          │
  │  ✔ Minimum-permission subagents         │  │  1. Standardize metric threshold gates  │
  │  ✔ Hardcoded ML guardrails              │  │  2. Expand autoresearch to more tasks   │
  │  ✔ 13 reusable, independently updatable │  │  3. Wire drift monitoring post-deploy   │
  │    skills decoupled from agents         │  │  4. Adapt the pattern to your team's    │
  │  ✔ Config-only drop-in, any ML repo     │  │     domain — orchestration stays same   │
  └─────────────────────────────────────────┘  └─────────────────────────────────────────┘
```

---

## Slide 12: Live Demo

### Visual Layout: Demo Script Card

- **Structure:** A clear demo script showing the command to run, what the audience should watch for at each step, and the expected output — so the demo reads as a narrative even if something goes wrong.
- **Color Palette:** Deep Navy (command) → Teal (steps) → Forest Green (output).

### Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│   DEMO: Full EDA → Plan → Build → Review cycle via OpenCode                  │
└────────────────────────────────────────────────────────────────────────────────┘

  STEP 1 — Trigger EDA                          WATCH FOR
  ─────────────────────────────────────────     ──────────────────────────────────
  /eda data/features.parquet                    ml-orchestrator routes to
                                                ml-data-analyst (not a general LLM)
                                                ml-eda skill loads on demand
                                                profile-dataset.py runs read-only
                                                Leakage flags surfaced automatically

  STEP 2 — Plan an experiment                   WATCH FOR
  ─────────────────────────────────────────     ──────────────────────────────────
  /train                                        ml-orchestrator invokes planner
                                                BEFORE any code is written
                                                sequential-thinking MCP engaged
                                                Karpathy principles applied live:
                                                "simplest model that meets criteria"

  STEP 3 — Review the changes                   WATCH FOR
  ─────────────────────────────────────────     ──────────────────────────────────
  /review-ml                                    ml-code-reviewer (read-only, isolated)
                                                Checks: str_to_bool · leakage guards
                                                · MLflow run management · YAML sync
                                                CRITICAL / WARNING / SUGGESTION output

┌────────────────────────────────────────────────────────────────────────────────┐
│  Expected output: dataset-profile.md · experiment-plan.md · structured review  │
│  No files modified without explicit builder invocation. Full action log saved.  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### Slide Content

- If demo environment is unavailable, the diagram above serves as the walkthrough — each step maps to a real output shown in Slide 8.

---
*6 subagents · 13 skills · 9 slash commands · Azure ML · OpenCode — one config-only setup powering the full ML SDLC.*
