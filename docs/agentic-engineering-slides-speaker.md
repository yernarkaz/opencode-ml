## Slide 1. What is Agentic Engineering and What it does

### On-slide bullets

- AI agents execute ML workflow stages with clear roles
- Orchestrator routes work to specialist agents and skills
- Built for Azure ML delivery with guardrails by default

### Speaker notes

Agentic engineering means we stop treating AI as only a chat assistant and instead use it as a structured execution system. In this repo, one orchestrator agent receives the request, then routes it to specialist agents for planning, data analysis, code implementation, review, or autonomous experimentation. The result is an ML workflow that is faster, more consistent, and safer than ad hoc prompting.

For Azure ML specifically, this repo covers the full path from data exploration to training, evaluation, deployment, and monitoring. The important point is that agents are not acting freely. They operate inside explicit rules, scoped permissions, and stage-specific patterns.

## Slide 2. High-Level Value Proposition

### On-slide bullets

- Faster ML iteration
- Lower delivery risk
- More repeatable engineering workflows
- Easier onboarding across repos

### Speaker notes

The value proposition is simple. First, it speeds up ML engineering by turning common tasks into reusable workflows through slash commands, agents, and skills. Second, it reduces risk by enforcing good practices such as planning before implementation, code review after changes, and controlled promotion through development, QA, and production.

It also improves repeatability. Instead of every repo inventing its own workflow, this template gives teams a shared operating model. That is especially useful for onboarding, because new repos inherit the same structure, terminology, tools, and guardrails.

## Slide 3. The N-Phase Execution Workflow

### On-slide bullets

- Plan
- Explore data
- Cleanse and validate
- Implement
- Train and evaluate
- Review
- Deploy and monitor
- Autoresearch loop

### Speaker notes

This repo follows a staged execution model. It starts with planning, where the experiment planner defines the objective, risks, steps, and success criteria. Then the data analyst profiles the data and identifies leakage, nulls, skew, and data quality issues. After that, data cleansing and validation can be applied before code changes are made.

Implementation is handled by the write-capable code builder, but only after planning. Training and evaluation then use MLflow-aware tools to capture metrics and compare outcomes. Review comes next, which is important because the design of this repo expects review after implementation, not as an optional extra.

Finally, deployment happens through a gated D to Q to P workflow, followed by monitoring. If needed, the autoresearch agent can run repeated improve-measure-keep-or-discard cycles to push metrics further.

## Slide 4. Output: What you get

### On-slide bullets

- Structured plans and EDA reports
- Minimal validated code changes
- Training and evaluation results
- Deployment and monitoring outputs
- Autoresearch logs and winning experiments

### Speaker notes

This system produces concrete engineering outputs, not just suggestions. On the analysis side, you get structured plans and EDA findings. On the implementation side, you get actual code changes that follow the repo’s ML patterns and are backed by tests.

On the operations side, you get training metrics, MLflow run information, deployment guidance, smoke-test expectations, and monitoring actions. In autonomous experimentation mode, you also get a trace of tested hypotheses, measured deltas, and a record of which changes were kept or discarded.

## Slide 5. Architecture

### On-slide bullets

- `opencode.json` sets model, permissions, MCP, default agent
- Plugins inject environment, tools, and compaction state
- Orchestrator delegates to specialist subagents
- Skills and tools provide stage-specific execution support

### Speaker notes

At the center is `opencode.json`. It defines the default agent, the permission model, the MCP servers, and protections like `share: disabled` and `snapshot: false`. Around that, plugins provide runtime support. One plugin injects `PYTHONPATH`, another registers the custom ML tools, and another preserves critical ML context across session compaction.

Above that sits the orchestrator agent, which delegates to specialist subagents such as the planner, analyst, code builder, reviewer, and autoresearch agent. Skills then act as focused knowledge packs for specific stages like EDA, evaluation, deployment, or monitoring. Underneath, tool-backed Python scripts connect the agent layer to MLflow and Azure ML job state.

## Slide 6. How do agents and skills interact

### On-slide bullets

- Orchestrator decides who should act
- Subagents own execution by stage
- Skills add task-specific patterns and checklists
- Tools provide structured data back to agents

### Speaker notes

The interaction model is layered. The orchestrator decides which subagent should handle a given stage. The subagent then performs the work appropriate for that stage. If more specialization is needed, it loads a skill that provides workflow guidance, gotchas, scripts, or evaluation criteria.

Tools are the execution bridge. For example, agents can call `profile_dataset` for data profiling, `run_mlflow_query` for experiment data, and `check_training` for Azure ML job status. This means the agent is not guessing. It is making decisions using structured information returned from tools.

## Slide 7. Key Guardrails & System safety

### On-slide bullets

- Read-only vs write-capable agent separation
- Ask-before-run protection for risky commands
- ML coding rules enforced by builder and reviewer
- Deployment gates prevent unsafe promotion

### Speaker notes

Guardrails are one of the strongest parts of this repo. Planning, analysis, and review agents are read-only. Only the code builder and autoresearch agent can edit files and run shell commands. Even then, risky commands such as `az ml`, package installs, destructive git actions, or `rm` are protected by ask rules in the config.

At the code level, the repo encodes ML-specific safety checks such as no temporal leakage, `str_to_bool` for AML-compatible booleans, correct MLflow run handling, and strict D to Q to P deployment sequencing. This is important because the system is not only accelerating work. It is constraining work to safe and repeatable patterns.

## Slide 8. ML Agentic Engineering workflow

### On-slide bullets

- Start with a business or model goal
- Route to plan, analyze, build, evaluate, review
- Promote only after evidence and checks
- Monitor in production and iterate

### Speaker notes

In practice, the workflow starts when a user describes a problem such as improving a metric, understanding a dataset, fixing a training issue, or preparing a deployment. The orchestrator translates that request into the right sequence of actions.

The key value is that the repo encodes good ML delivery order: first understand the objective, then inspect data, then implement carefully, then measure, then review, then deploy, then monitor. That sequence reduces wasted experimentation and catches issues earlier. If the model still needs improvement, the autoresearch loop can continue iterating using explicit keep-or-discard rules.

## Slide 9. Summary including (how useful it is and things to improve)

### On-slide bullets

- Highly useful as an ML delivery operating model
- Strong on structure, safety, and repeatability
- Best next step: strengthen project-level adoption assets

### Speaker notes

Overall, this repo is very useful because it turns Azure ML engineering into a structured operating model instead of a collection of disconnected prompts and scripts. Its strengths are role separation, explicit workflow stages, strong guardrails, and direct integration with practical ML tasks like profiling, MLflow analysis, job monitoring, evaluation, and deployment.

The main improvements are about adoption maturity. First, when this template is applied to a real project, `opencode.json` should include the relevant docs in `instructions` so domain context is always available in-session. Second, the presentation layer could benefit from a visual architecture diagram rather than ASCII. Third, downstream starter assets such as test scaffolds, deployment example files, and evaluation threshold configuration would make onboarding even smoother.

## Optional Closing Slide. One-line Takeaway

### On-slide bullets

- Agentic engineering makes Azure ML workflows faster, safer, and more repeatable

### Speaker notes

If I had to summarize this repo in one sentence, it is a reusable agent-based control layer for Azure ML engineering. It helps teams move faster, but without giving up discipline, traceability, or deployment safety.
