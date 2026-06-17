# ML Agentic Engineering — PPT Slide Deck Visual Designs

This document contains the visual slide layouts, diagrams, and blueprints for the PowerPoint slides. The designs below are styled based on concrete enterprise slide patterns: **Horizontal Timelines**, **Gated Flow Sandboxes**, **Card Decks**, and **Safety Highlight Callouts**.

---

## Slide 1: What is Agentic Engineering and What it does

### 📊 Visual Layout Pattern: End-to-End Sandbox Flow (Image 4 Style)
*   **Structure:** A horizontal pipeline showing how raw, risky manual tasks are ingested, compiled in an orchestrated subagent sandbox, and outputted as secure, validated assets.
*   **Color Palette:** Cold Gray (Inputs) → Warning Crimson (Sandbox Execution) → Deep Green (Target Outputs).

### 🎨 Diagram Blueprint

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                            │
│   LEGACY INPUT                       ORCHESTRATOR EXECUTION                 TARGET OUTPUT  │
│  ┌──────────────────────┐  PARSE   ┌───────────────────────────┐  VALIDATE ┌─────────────┐ │
│  │ Ad-hoc CLI commands   │ ───────►│  Main Agent + Subagents   │ ─────────►│ Clean Code  │ │
│  │ Temporal leakage risk│         │  Role-specialized sandbox │           │ Zero-leakage│ │
│  │ Manual arg errors    │         │  (ml-orchestrator)        │           │ Tested YAML │ │
│  └──────────────────────┘         └───────────────────────────┘           └─────────────┘ │
│                                                                                            │
│   End-to-End Delivery: Converts manual, risk-prone pipeline commands into verified,        │
│   consistent, and safe Azure ML assets under automatic guardrails.                         │
│                                                                                            │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 30, 'padding': 10}} }%%
graph LR
    A["Manual ML work"] -->|route| B["ml-orchestrator"] --> C["Specialist agents"] -->|verify| D["Safe ML outputs"]
    N1["CLI runs<br/>Leakage risk<br/>Arg errors"]:::legacy --- A
    N2["Plan<br/>Build<br/>Review"]:::orchestrator --- C
    N3["Tested code<br/>Valid YAML<br/>Zero leakage"]:::target --- D

    classDef legacy fill:#F1F5F9,stroke:#64748B,stroke-width:2px,color:#0F172A;
    classDef orchestrator fill:#FEF2F2,stroke:#DC2626,stroke-width:2.5px,color:#991B1B;
    classDef target fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#15803D;

    class A,N1 legacy;
    class B,C,N2 orchestrator;
    class D,N3 target;
    linkStyle 2,3,4 stroke-width:0px;
```

### 📝 Slide Content

*   **Agentic Engineering:** Autonomous, role-specialized software agents executing ML workflows with guardrails.
*   **Template Scope:** Scaffolds, plans, profiles, writes code, reviews, and deploys.
*   **Core Outcomes:** Zero-leakage code, validated component parameters, and repeatable D→Q→P promotion.

---

## Slide 2: High-Level Value Proposition

### 📊 Visual Layout Pattern: Horizontal Card Grid (Image 2 Style)

*   **Structure:** 4 clean, separate cards with bold titles, visual symbols, and crisp body text arranged side-by-side or in a 2x2 grid.
*   **Color Palette:** Charcoal Blue headers, Light Slate card fills, deep Navy text.

### 🎨 Diagram Blueprint

```text
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 🚀 ACCELERATED ML DELIVERY     │   │ 🛡️ BUILT-IN QUALITY & GATES    │
│                               │   │                               │
│ Direct slash commands (/train,│   │ Strict policies for leakage,  │
│ /eda, /deploy) remove human   │   │ argument matching, and        │
│ overhead and speed up feedback│   │ chronological splits are      │
│ loops instantly.              │   │ hardcoded into the sandbox.   │
└───────────────────────────────┘   └───────────────────────────────┘
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ 👁️ OBSERVABILITY & METRICS     │   │ 📦 PORTABLE DROP-IN SETUP      │
│                               │   │                               │
│ Automatic MLflow tracking URI │   │ Config-only workspace drops   │
│ discovery, training job       │   │ into any repo; schemas adapt  │
│ polling, and metrics reporting│   │ via simple Markdown files in  │
│ are fully standardized.       │   │ docs/.                        │
└───────────────────────────────┘   └───────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#CBD5E1'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 30, 'rankSpacing': 30, 'padding': 15}} }%%
graph TB
    A["<b>🚀 Accelerated ML Delivery</b><br/><br/>Direct slash commands like /train,<br/>/eda, and /deploy reduce manual<br/>overhead and speed up loops."]:::blue
    B["<b>🛡️ Built-in Quality and Gates</b><br/><br/>Leakage rules, argument validation,<br/>and chronological splits are<br/>enforced inside the sandbox."]:::red
    C["<b>👁️ Observability and Metrics</b><br/><br/>MLflow URI discovery, job polling,<br/>and metric reporting are<br/>standardized across the workflow."]:::teal
    D["<b>📦 Portable Drop-in Setup</b><br/><br/>A config-only workspace can drop<br/>into any repo and adapt through<br/>docs and schema templates."]:::amber

    A ~~~ B
    C ~~~ D
    A --- C
    B --- D

    classDef blue fill:#F8FAFC,stroke:#2563EB,stroke-width:2px,color:#0F172A;
    classDef red fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#0F172A;
    classDef teal fill:#F0FDFA,stroke:#0D9488,stroke-width:2px,color:#0F172A;
    classDef amber fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#0F172A;
    linkStyle 0,1,2,3 stroke-width:0px;
```

---

## Slide 3: The N-Phase Execution Workflow

### 📊 Visual Layout Pattern: Milestone Timeline with Callout Banner (Image 1 Style)
*   **Structure:** A continuous chronological flow with numbered milestone circles, paired with an emergency red policy-gate warning banner at the bottom.
*   **Color Palette:** Warm Gray path, Slate node fills, Bright Red warning stop.

### 🎨 Diagram Blueprint

```text
   ( 01 ) ──────── ( 02 ) ──────── ( 03 ) ──────── ( 04 ) ──────── ( 05 ) ──────── ( 06 ) ──────── ( 07 )
    Plan            EDA           Cleanse          Build         Evaluate         Review          Deploy
   Plan first,     Profile        Validate         Minimal         Track          Review code    D -> Q -> P
   define goals   datasets        raw data         pipeline       MLflow          before merge   idempotency


┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  🛑 MANDATORY GOVERNANCE STOPS: Experiment Planning (Phase 1) and Code Review (Phase 6) must pass      │
│     successfully before any deployment or pipeline promotion is permitted.                             │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 15, 'rankSpacing': 25, 'padding': 10}} }%%
graph TB
    subgraph Flow ["A"]
        direction LR
        P1((Plan)) --> P2((EDA)) --> P3((Clean)) --> P4((Build)) --> P5((Eval)) --> P6((Review)) --> P7((Deploy)) --> P8((Monitor))
    end
    G["Mandatory gates:<br/>Plan and Review must pass"]:::warn
    P1 -.-> G
    P6 -.-> G

    classDef step fill:#1E3A8A,stroke:#172554,stroke-width:2px,color:#FFFFFF;
    classDef gate fill:#DC2626,stroke:#991B1B,stroke-width:2px,color:#FFFFFF;
    classDef warn fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B;

    class P2,P3,P4,P5,P7,P8 step;
    class P1,P6 gate;
```

---

## Slide 4: Output: What you get

### 📊 Visual Layout Pattern: Split Process-to-Artifact Layout (Image 5 Style)
*   **Structure:** Left pane shows the input source and active agent processes; right pane displays a vertical stack of clean, pill-shaped cards representing the generated deliverables.
*   **Color Palette:** Cool Blue (Process) → Forest Green (Deliverable Pillboxes).

### 🎨 Diagram Blueprint

```text
   INPUT PROCESS                           OUTCOME ARTIFACTS
  ┌─────────────────────────┐             ┌─────────────────────────────────────────────────┐
  │  User Request           │             │  📄 structured-experiment-plan.md               │
  │  (Modify feature list)  │             └─────────────────────────────────────────────────┘
  │                         │             ┌─────────────────────────────────────────────────┐
  │           ▼             │             │  📊 dataset-profiling-report.json               │
  │  ORCHESTRATOR ROUTING   │             └─────────────────────────────────────────────────┘
  │  Planner  ──► Builder   │             ┌─────────────────────────────────────────────────┐
  │  Reviewer ──► Deployer  │             │  🛠️ ruff-validated, tested-pipeline-diffs       │
  │                         │             └─────────────────────────────────────────────────┘
  │           ▼             │             ┌─────────────────────────────────────────────────┐
  │  SUCCESS CRITERIA MET   │             │  📈 mlflow-run-metrics-and-artifacts            │
  │  Unit tests: PASS       │             └─────────────────────────────────────────────────┘
  │  YAML validation: PASS  │             │  🚀 active-dev-online-endpoint-smoke-test       │
  └─────────────────────────┘             └─────────────────────────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 20, 'padding': 10}} }%%
graph LR
    subgraph Process ["Process"]
        direction TB
        A["User request"] --> B["Orchestrator routing"] --> C["Tests and validation"]
    end

    subgraph Deliverables ["Outputs"]
        direction TB
        D["Design Plan"]
        E["EDA report"]
        F["Tested code"]
        G["MLflow metrics"]
        H["Endpoint test"]
    end

    C -->|deliver| D
    D ~~~ E
    E ~~~ F
    F ~~~ G
    G ~~~ H

    classDef proc fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef pill fill:#F0FDF4,stroke:#16A34A,stroke-width:1.5px,color:#14532D;

    class A,B,C proc;
    class D,E,F,G,H pill;
```

---

## Slide 5: Architecture

### 📊 Visual Layout Pattern: Layered Tech Stack Blocks
*   **Structure:** Block diagram showing the core configuration, the orchestration layer, custom plug-ins, and how they interface with external tooling (MLflow / Azure ML).
*   **Color Palette:** Slate Blue (Control) → Teal Green (Integration).

### 🎨 Diagram Blueprint

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│  USER INTERFACE: Slash Commands (/eda, /train, /evaluate, /deploy, /monitor)               │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  CONTROL LAYER: Orchestrator Agent (ml-orchestrator) & Specialized Subagents              │
│  ┌───────────────────────┐ ┌───────────────────────┐ ┌──────────────────────────────────┐ │
│  │ ml-experiment-planner │ │ ml-code-builder       │ │ ml-autoresearch                  │ │
│  │ (thinking, read-only) │ │ (write-capable: edit) │ │ (modify-train-measure loop)     │ │
│  └───────────────────────┘ └───────────────────────┘ └──────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  EXTENSION PLUGINS & BACKING SCRIPTS (PEP 723 / uv run)                                   │
│  ┌──────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────────┐ │
│  │ ml-env (PYTHONPATH)      │ │ ml-tools (profile, runs) │ │ ml-compaction (state save) │ │
│  └──────────────────────────┘ └──────────────────────────┘ └────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  ON-DEMAND SKILLS (.agents/skills/*): Cleansing, Evaluation, Deployment, Monitoring        │
├───────────────────────────────────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE INTERFACE: Azure ML CLI v2 & MLflow Tracking Workspace APIs               │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 25, 'padding': 10}} }%%
graph TB
    A["Slash commands"] --> B["ml-orchestrator"] --> C["Subagents"] --> D["Skills"] --> E["Tools + plugins"] --> F["Azure ML + MLflow"]
    G["Docs templates"] -.-> B

    classDef ui fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef control fill:#FEF2F2,stroke:#DC2626,stroke-width:2px,color:#991B1B;
    classDef ext fill:#F0FDFA,stroke:#0D9488,stroke-width:2px,color:#115E59;
    classDef infra fill:#F8FAFC,stroke:#CBD5E1,stroke-width:2px,color:#0F172A;

    class A,G ui;
    class B,C,D control;
    class E ext;
    class F infra;
```

---

## Slide 6: How do agents and skills interact

### 📊 Visual Layout Pattern: Dynamic Pipeline Sequence Flow (Image 4 Style)
*   **Structure:** Flowchart tracing the step-by-step resolution of a slash command, showing how the Orchestrator pairs agents with explicit on-demand skills.
*   **Color Palette:** Slate Blue (Agent Core) → Deep Teal (Skill Execution).

### 🎨 Diagram Blueprint

```text
  [ Slash Command ] ──────► [ Orchestrator ] ──────► [ Specialist Subagent ]
    e.g., /deploy            ml-orchestrator           ml-code-builder
                                                             │
                                                             ▼ Loads (On-Demand)
                                                     ┌────────────────────────┐
                                                     │ ml-deployment Skill    │
                                                     │ - Checklists & gotchas │
                                                     │ - scripts/deploy.py    │
                                                     └────────────────────────┘
                                                             │
                                                             ▼ Executes
                                                     [ Azure ML CLI v2 / Tools ]
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 30, 'padding': 10}} }%%
graph LR
    A["Slash command"] --> B["Orchestrator"] --> C["Subagent"] --> D["Skill"] --> E["Tools"] --> F["Azure ML"]
    D -.-> G["Checklists<br/>+ gotchas"]

    classDef agent fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef skill fill:#F0FDFA,stroke:#0D9488,stroke-width:2px,color:#115E59;
    classDef output fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#14532D;

    class A,B,C agent;
    class D,G skill;
    class E,F output;
```

---

## Slide 7: Key Guardrails & System Safety

### 📊 Visual Layout Pattern: Warning Banner with Checklists (Image 3 Style)
*   **Structure:** Highlighted red banner with lock icon for "Safety-First Engineering", followed by 4 detailed, checkmarked items in columns below.
*   **Color Palette:** Alert Crimson (Banner) → Teal & Navy (Checklist items).

### 🎨 Diagram Blueprint

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│  🔒 Safety-First Engineering                                                              │
│  Automated sandboxing and guardrails ensure agents operate strictly in safe boundaries.   │
└───────────────────────────────────────────────────────────────────────────────────────────┘

  ✔ SCOPED WRITE PERMISSIONS                  ✔ ENFORCED CODING PATTERNS
    Only Builder & Autoresearch can edit        str_to_bool for booleans, Managed Identity,
    files; Orchestrator, Planner, and Analyst   no hardcoded tracking URIs, chronological
    are locked to read-only mode.               temporal leakage guards.

  ✔ RISKY COMMAND FILTERS                     ✔ GATED PROMOTION FLOWS
    High-risk commands (rm, git push/reset,     D -> Q -> P environments cannot be skipped;
    az ml) are caught by opencode.json          scoring scripts must be tested locally
    and trigger manual human prompts.           with sample payloads first.
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 20, 'padding': 10}} }%%
graph TB
    A["Safety-First Engineering"]:::warn
    subgraph R1 [" "]
        direction LR
        B["Scoped write<br/>permissions"]:::rail
        C["ML coding<br/>rules"]:::rail
    end
    subgraph R2 [" "]
        direction LR
        D["Risky command<br/>prompts"]:::rail
        E["D -> Q -> P<br/>gates"]:::rail
    end
    A ~~~ RowSpace
    RowSpace ~~~ R1
    RowSpace ~~~ R2
    A --- R1
    A --- R2

    classDef warn fill:#FEF2F2,stroke:#DC2626,stroke-width:2.5px,color:#991B1B;
    classDef rail fill:#F8FAFC,stroke:#CBD5E1,stroke-width:1.5px,color:#0F172A;
    style RowSpace fill:none,stroke:none;
    linkStyle 2,3 stroke-width:0px;
```

---

## Slide 8: ML Agentic Engineering Workflow

### 📊 Visual Layout Pattern: Flow Timeline with Parallel Channels
*   **Structure:** Step-by-step user session showing the handoffs from design, to sandbox validation, to deployment.
*   **Color Palette:** Indigo (User-focused) → Green (Validated output).

### 🎨 Diagram Blueprint

```text
  [ User Goal ]
       │
       ▼
  Phase 1: Design  ──────► ml-experiment-planner produces design specification
       │
       ▼
  Phase 2: Profile ──────► ml-data-analyst profiles dataset for leakage risks
       │
       ▼
  Phase 3: Build   ──────► ml-code-builder writes pipeline code and runs unit tests
       │
       ▼
  Phase 4: Review  ──────► ml-code-reviewer flags CRITICAL/WARNING issues
       │
       ▼
  Phase 5: Deploy  ──────► ml-deployment promotes model to D -> Q -> P
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 25, 'padding': 10}} }%%
graph LR
    U(["User goal"]) --> P1["Plan"] --> P2["Profile"] --> P3["Build"] --> P4["Review"] --> P5["Deploy"]
    P1 -.-> S1["planner"]
    P2 -.-> S2["analyst"]
    P3 -.-> S3["builder"]
    P4 -.-> S4["reviewer"]
    P5 -.-> S5["deployment skill"]

    classDef phase fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef actor fill:#F8FAFC,stroke:#64748B,stroke-width:1.5px,color:#0F172A;

    class U,P1,P2,P3,P4,P5 phase;
    class S1,S2,S3,S4,S5 actor;
```

---

## Slide 2: Summary

### 📊 Visual Layout Pattern: Side-by-Side Card Deck (Image 2 Style)
*   **Structure:** Two massive, clean, vertical panels displaying the "Core Strengths" and the "Path to Maturity" respectively.
*   **Color Palette:** Soft Blue-Green (Value) → Soft Amber (Future Improvements).

### 🎨 Diagram Blueprint

```text
  ┌─────────────────────────────────────────┐   ┌─────────────────────────────────────────┐
  │  🌟 WHAT WORKS: STRENGTHS & VALUE       │   │  🚀 NEXT STEPS: AREAS TO IMPROVE        │
  ├─────────────────────────────────────────┤   ├─────────────────────────────────────────┤
  │                                         │   │                                         │
  │  ✔ Separation of Concerns: Read-only    │   │  1. In-Session Conventions: Auto-load   │
  │    planners and analysts prevent        │   │     docs/ schemas into opencode.json    │
  │    accidental codebase disruption.      │   │     instructions key.                   │
  │                                         │   │                                         │
  │  ✔ Hardcoded Guardrails: Key ML pitfalls│   │  2. Evaluation Gates: Standardize metric│
  │    (temporal leakage, bad booleans)     │   │     threshold configs in a shared JSON. │
  │    are blocked automatically.           │   │                                         │
  │                                         │   │  3. Expand Monitoring: Add baseline     │
  │  ✔ Out-of-the-Box Tooling: Profile and  │   │     drift schedules and alerting rules  │
  │    MLflow utilities speed up loop.      │   │     as a downstream starter asset.      │
  │                                         │   │                                         │
  └─────────────────────────────────────────┘   └─────────────────────────────────────────┘
```

### 🧜‍♂️ Mermaid Flowchart

```mermaid
%%{init: {'theme':'base','themeVariables': {'fontSize':'14px','fontFamily':'Aptos, Arial, sans-serif','primaryTextColor':'#0F172A','lineColor':'#94A3B8'}, 'flowchart': {'curve': 'linear', 'nodeSpacing': 20, 'rankSpacing': 20, 'padding': 10}} }%%
graph LR
    subgraph Strengths ["🌟 CORE STRENGTHS & VALUE"]
        direction TB
        A["✔ Role Separation<br/>Read-only planners prevent accidental disruption."]
        B["✔ Safety Guardrails<br/>Blocks temporal leakage and bad boolean arg flags."]
        C["✔ Integrated Tooling<br/>Ready-to-use profiling and MLflow tracking."]
    end

    subgraph Future ["🚀 PATH TO MATURITY"]
        direction TB
        D["1. Convention Context<br/>Auto-load schemas into session instructions."]
        E["2. Metric Thresholds<br/>Centralize gate configs in shared JSON stubs."]
        F["3. Monitoring Logic<br/>Expand drift alert schedules and telemetry."]
    end

    classDef strength fill:#F0FDF4,stroke:#16A34A,stroke-width:2px,color:#14532D;
    classDef improvement fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#78350F;

    class A,B,C strength;
    class D,E,F improvement;
```

---
*Generated based on OpenCode ML agentic configurations.*
