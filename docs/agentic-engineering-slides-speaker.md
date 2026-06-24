## Slide 1. What is Agentic Engineering & How We Got Here

### On-slide bullets

- AI as Copilot → things go wrong → purpose-built agentic SDLC
- Software 3.0: LLMs as the runtime, not just the assistant
- 6 locked specialists · 13 skills · 9 commands · Azure ML
- Karpathy's principles hardcoded, not suggested

### Speaker notes

Let me start by telling you how this actually began — because it was not a planned architecture. It started exactly the way that banner describes: someone said "let's just add an AI assistant to our ML pipelines." So we did. The assistant wrote some code, we ran it manually, and honestly, it felt great. Productive. Promising.

Then we gave it a bit more access. And that is where things started to unravel.

Without clear roles, without guardrails, without any kind of audit trail, the agent began modifying files it was never supposed to touch. It ran commands no one had asked for. And because nothing was logged, we could not reliably tell what had changed or why. That is Stage 2 on this slide — and if you are honest with yourselves, a lot of teams are living in Stage 2 right now and calling it AI-assisted development. It looks productive. It is also fragile.

Andrej Karpathy describes this era as Software 3.0. Software 1.0 was hand-written logic. Software 2.0 was behaviour learned by neural networks. Software 3.0 is programming in plain language, where large language models serve as the runtime. That is a genuine shift. But hooking an LLM to a codebase with no structure around it does not get you Software 3.0. It gets you a fast way to introduce hard-to-trace changes.

Agentic Engineering is what Software 3.0 looks like when it is built responsibly. Not one model you prompt, but a small team of specialists you orchestrate — each one with a defined role, scoped permissions, and a clear boundary for what it is and is not allowed to do. Six subagents. Thirteen skills. Nine commands. That is Stage 3, and that is what we are going to walk through today.

---

## Slide 2. Value Proposition

### On-slide bullets

- Speed: ML feedback loops from hours to minutes
- Quality: temporal leakage and str_to_bool checked automatically
- Consistency: same steps, same guardrails, every run
- Transparency: complete, readable audit trail for every agent action

### Speaker notes

AI tooling value propositions tend to sound alike — faster, better, more consistent. So let me be specific about what that actually means here, because the specifics are what make it worth caring about.

Speed is the obvious one. Running /eda on a dataset gives you a full profile — null rates, skew, cardinality, leakage flags — without writing a single line of profiling code. Running /train kicks off a sequence that plans the experiment, implements the pipeline, runs a review, and hands you a diff to approve. Workflows that used to take half a day of context-switching now take minutes.

Quality is actually the more interesting one, and it is the one people tend to underestimate. ML codebases have very specific correctness requirements that are subtle enough to slip through even careful code review. One example: Azure ML passes boolean argument values as strings from component YAML files, so the standard Python store_true flag silently breaks when deployed. You need a helper called str_to_bool instead. Another: every feature aggregation that looks back in time needs a guard to prevent data from the future leaking into training. These are not things most reviewers catch under time pressure. This system checks them automatically, every time.

Consistency is underrated as a value. When every workflow follows the same path — same agent sequence, same review gate, same deployment order — new team members do not need to learn the tribal knowledge to do things correctly. The process is encoded in the system, not in someone's head.

And transparency is what makes all three of those sustainable. Every agent action is logged. Every tool call, every decision, every output forms a readable trail. That is what lets you trust the system, and what lets you investigate it when something needs explaining.

---

## Slide 3. Core Concepts Demystified

### On-slide bullets

- Agent: autonomous specialist with scoped tool access
- Orchestrator: routes tasks to the right agent
- Skill: domain-specific rulebook loaded on demand
- Guardrail: enforced constraint — "az ml *": "ask" · edit: deny
- Command: triggers a full multi-agent workflow
- Plugin: session-scoped hook that injects context or tools

### Speaker notes

Before we get into the architecture, it helps to agree on what these terms actually mean — because they get used very loosely in the industry, and the distinctions matter here.

An agent is not just a wrapper around a language model. It is a specialist with a defined role, specific tools it can access, and explicit constraints on what it may and may not do. In this system, the data analyst can run Python scripts but cannot edit files. The code builder can edit files but has to ask permission before running any Azure ML commands. These are not just labels — they are enforced boundaries.

The orchestrator is the entry point. It does not do the actual work. It looks at a request, decides which specialist should handle it, routes accordingly, and enforces the required sequence. Think of it as a dispatcher who also makes sure work happens in the right order.

A skill is a focused rulebook that an agent loads when it needs domain-specific knowledge. When the data analyst loads the ml-eda skill, it gets the rules for spotting leakage, the thresholds for null checks, the pattern for auditing time-based features. Skills are loaded on demand and can be updated independently — if a pipeline pattern changes, you update the skill file, not the agent.

Guardrails are where things get concrete. The example in this table comes straight from the actual config: "az ml *": "ask" in the global permission file, and edit: deny in the agent's own configuration. These are not recommendations. An agent that tries to run an Azure ML command stops and waits for a human to confirm. A read-only agent that tries to modify a file is blocked outright.

Commands are the user interface — /eda, /train, /deploy, /review-ml. Each one triggers a full multi-agent workflow. They are the only thing you need to know to use the system.

---

## Slide 4. The Execution Lifecycle

### On-slide bullets

- 7 phases: Plan · Analyze · Build · Test · Review · Deploy · Monitor
- Actual slash commands shown per phase
- Governance gates at Plan and Review — mandatory before deployment
- Same lifecycle for ML, software, QA, and BA workflows

### Speaker notes

This is the workflow — seven phases — and the ordering matters as much as the steps themselves.

It starts with planning. Before a single line of code is written, the experiment planner defines the objective, the risks, the steps, and the success criteria. This is not optional. The system enforces it: you cannot reach the build phase without a completed plan. That might feel like overhead, but it is one of the most valuable constraints in the whole system. It directly applies Karpathy's first principle — think before coding.

Data analysis comes next. The data analyst profiles the dataset, flags leakage risks, checks distributions, identifies quality issues. This is the cheapest place to catch problems. A leakage issue found here takes minutes to fix. The same issue found in production requires a model rollback.

Only then does implementation begin. The code builder writes against the patterns defined in the skills. The reviewer follows immediately, producing structured output — CRITICAL findings that block deployment, WARNING findings that require a decision. These are gates, not suggestions.

Deployment follows the Dev-to-QA-to-Prod sequence, with human confirmation required at each Azure ML command. And the cycle continues post-deployment through monitoring and, when needed, an autonomous experiment loop that can run overnight and surface the best result for human review.

The last thing worth saying about this slide: this lifecycle is not exclusive to ML engineering. The same seven phases apply to software feature delivery, QA test planning, and business analysis workflows. The commands and agents change by domain. The structure stays the same.

---

## Slide 5. Architecture & How it Works

### On-slide bullets

- Layer 1: 9 slash commands — the user interface
- Layer 2: ml-orchestrator — routes and governs
- Layer 3: 5 specialist subagents with model-level assignments
- Layer 4: 13 skills · 3 plugins · 3 tools
- Layer 5: Azure ML · MLflow · Online Endpoints · D → Q → P
- Request trace: /eda through all 5 layers in 4 steps

### Speaker notes

Let me walk you through what actually happens when you run a command.

The top layer is the user interface — nine slash commands. Every workflow starts here. That is the only surface you interact with directly.

Below that is the orchestrator. It runs on the lightest model in the configuration, because routing decisions do not need heavy reasoning. It is read-only, meaning it cannot make any changes itself. Its job is to look at the command, understand the intent, and hand the work to the right specialist. It cannot bypass its own agent allowlist, and it cannot be skipped.

The specialist layer is where the real work happens. Five agents, each assigned a model matched to the demands of their role. The experiment planner runs on the most capable reasoning model, because planning is the highest-stakes step. The code builder and autoresearch agent run on a mid-tier model appropriate for implementation work. The data analyst and reviewer run on the lightest model, because their tasks are well-structured and can be done at high quality and lower cost.

Below the agents are thirteen skills, three plugins, and three Python tools. The plugins handle the setup work: injecting the Python environment, registering custom tools, and preserving ML context when the session gets long. The tools return structured data directly to agents — dataset profiles, MLflow run results, training job status — so agents are making decisions on reliable information rather than guessing from unstructured output.

At the bottom is the infrastructure: Azure ML, MLflow, online endpoints, and the gated deployment sequence.

Here is a concrete trace. You run /eda on a parquet file. The orchestrator sees "explore" and routes to the data analyst. The data analyst loads the ml-eda skill, gets the leakage rules and null thresholds, calls profile-dataset.py with read-only access, and returns a structured report. Every step is logged. That is all five layers, end to end, for one command.

---

## Slide 6. Guardrails & Safety — How the Config Actually Works

### On-slide bullets

- Two-layer model: opencode.json global bash intercepts + per-agent frontmatter
- Last-match-wins: "*": "allow" first, specific "ask" overrides after
- edit: deny / edit: allow assigned per agent role
- ml-orchestrator task allowlist: only 2 named agents permitted
- Skills as a third layer: encode what correct looks like

### Speaker notes

Guardrails are the part of agentic systems that teams most often either skip or get wrong. And when people say they do not trust AI agents, what they usually mean is they do not trust unguarded agents with broad permissions. That is a reasonable concern. The answer is not to avoid agents — it is to design the constraints carefully.

This system uses two configuration layers. The first is the global config file — opencode.json — which intercepts bash commands. It starts with a wide-open default: everything is allowed unless otherwise specified. Then specific override rules follow. Commands like rm, git push, git reset, pip install, and any Azure ML command are set to "ask" — meaning the system stops and waits for a human to confirm before proceeding. The design principle here is last-match-wins: the wildcard sets the default, and specific rules selectively intercept only the commands worth pausing on. That is simpler to maintain than trying to explicitly allowlist every safe command.

The second layer is per-agent configuration. Each agent's file has its own permission block. The data analyst has edit: deny and bash: deny — it can read files, nothing else. The code builder has edit: allow and bash: allow, because it genuinely needs both. The orchestrator has a task allowlist — it can only invoke two named agents. Anything outside that list is blocked.

The table at the bottom makes this tangible. The data analyst running a Python script? Allowed — bash is permitted globally and this script is not on the intercept list. The data analyst trying to write a file? Blocked immediately by its own configuration. Any agent running an Azure ML job? Intercepted, human confirms. The orchestrator trying to spawn an unlisted agent? Blocked.

There is also a third layer that does not appear in the permission config at all: the skills. Skills encode what correct implementation looks like — the str_to_bool pattern, no hardcoded workspace URIs, leakage guards on time-based features, the right authentication credential for Azure. These are not permission rules. They are quality standards, enforced through the review gate. Permissions control what agents are allowed to run. Skills control what correct output looks like. Both matter.

---

## Slide 7. The 4 Core Workflows — Commands · Agents · Skills

### On-slide bullets

- EDA: ml-data-analyst + ml-eda skill → dataset profile with leakage flags
- Planning: ml-experiment-planner + sequential-thinking → structured experiment plan
- Build & Review: ml-code-builder + ml-code-reviewer → validated diffs + review findings
- Deploy & Monitor: ml-code-builder + ml-autoresearch → promoted endpoint + results.tsv

### Speaker notes

This is where the architecture becomes a daily workflow. Let me walk through each quadrant and show you what an ML engineer actually gets out of this.

The EDA quadrant is where most sessions start. You point /eda at a dataset and the data analyst loads its skill, runs the profiling tool, and returns a structured report — shape, null rates, skew, cardinality, top values per column. Leakage risk flags are included automatically, because the skill encodes the check. This is the kind of thing that human code review misses under time pressure, and it gets caught every single time here.

The planning quadrant is the one that feels most counterintuitive to engineers used to jumping straight to implementation. The experiment planner runs on the most capable model in the system, loads a reasoning tool, and applies four principles — think before coding, prefer simplicity, make surgical changes, stay goal-driven — to produce a structured plan before any code is touched. Objective, approach, risks, steps, acceptance criteria. The plan is what the code builder works from.

The build and review quadrant separates two things that often happen together in practice. The code builder implements. The reviewer follows independently — completely read-only, no bash access, no ability to modify anything — and returns structured findings. Every CRITICAL issue has a file, a line number, the problem, and the fix. CRITICALs block deployment. WARNINGs need a decision. The distinction is meaningful.

The deploy and monitor quadrant is where the system earns its depth. Deployment goes Dev to QA to Prod, with human sign-off required at each Azure ML command. Post-deployment, the monitoring skill watches for drift. And if the model needs improvement, the autoresearch agent can run an autonomous loop overnight — test a hypothesis, measure the result, keep or discard the change, log everything. It caps at ten training jobs, surfaces results as a cherry-pick, and never auto-merges. A human decides what goes forward.

---

## Slide 8. Role Applicability — The Same Pattern Across Teams

### On-slide bullets

- ML Engineer: 6 agents · 13 skills · promoted endpoint + metrics log
- Software Engineer: Architect · Builder · Test-Gen · Deployer → merged feature
- Business Analyst: Data Analyst · Req-Validator · Writer → stakeholder report
- QA Engineer: Test-Planner · Writer · Regression · Triager → test suite
- Common foundation: Orchestrator · Guardrails · Scoped Permissions · Audit Trail

### Speaker notes

This slide is here specifically because not everyone in this room works in ML, and I do not want anyone leaving thinking "interesting, but not for me."

The domain changes. The architecture does not.

Everything we have discussed — the orchestrator, the specialist agents, the permission model, the skills, the audit trail — none of that is specific to machine learning. It is a general pattern for running role-based automation with enforced constraints. ML is just the use case we built it for first.

For a software engineering team: the agents become an architect, a code builder, a test generator, and a deployer. Commands map to things like /feature, /review, /test, /deploy. Guardrails protect the main branch and enforce a review gate before merging. The output is a reviewed, tested feature with a clean audit trail.

For a business analyst team: agents handle data profiling, requirements validation, and documentation. Skills encode communication standards, completeness criteria for requirements, and documentation conventions. The output is a structured requirements document backed by actual data.

For a QA team: agents plan coverage, write test cases, run regression suites, and classify defects. Skills encode edge case patterns, severity criteria, and baseline comparison logic. The output is a complete test suite with a severity-classified defect list.

Every one of these configurations shares the same foundation: an orchestrator that governs the sequence, per-agent permission scoping, a skills layer that carries domain knowledge, and a full action log. Adopt the pattern, swap in your domain-specific agents and skills, and you get all of those properties without building the plumbing yourself.

---

## Slide 9. What You Get — Concrete ML Deliverables

### On-slide bullets

- EDA: dataset-profile.md — shape, nulls, skew, leakage flags
- Plan: experiment-plan.md — objective, steps, success criteria
- Build: ruff-validated diffs + unit tests + YAML sync confirmation
- Review: CRITICAL/WARNING/SUGGESTION findings with file and line
- Deploy: active endpoint + D→Q→P promotion log + smoke-test result
- Monitor/Autoresearch: results.tsv — hypothesis · Δmetric · KEPT/DISCARD

### Speaker notes

One of the main reasons people hesitate to trust agentic systems is that the outputs tend to be described vaguely. So let me walk through exactly what comes out of each stage — specifically, not generally.

After /eda: a markdown file. Dataset shape, column types, null rates, skew, cardinality, top five values per column, leakage risk flags with column names and explanations, and target distribution with class balance. It is a document you can share in a team review, attach to a ticket, or use as the basis for a planning conversation.

After the planning phase of /train: an experiment plan. Objective, approach with rationale, flagged risks, numbered steps, acceptance criteria. Not a chatbot transcript — a structured document that a human can approve, challenge, or push back on before a single line of code is written.

After the build phase: code diffs that are lint-formatted and passing. Unit tests in the right directory. And a confirmation that every ArgumentParser argument matches the corresponding entry in the component YAML. That last check matters because a mismatch there is a common source of Azure ML deployment failures that are genuinely painful to debug.

After /review-ml: a structured findings report. Every CRITICAL has a file path, a line number, the issue, and the fix. CRITICALs block deployment until they are resolved. WARNINGs have the same format and require a decision. This is a gate, not a suggestion.

After /deploy: an active endpoint, a promotion log showing Dev approved, QA approved, Prod deployed, and a smoke-test result confirming the endpoint is responsive.

After /autoresearch: a results.tsv file. Every row is one iteration — the hypothesis tested, the measured metric delta, and whether the change was kept or discarded. The best result comes back as a cherry-picked commit. Nothing moves forward without a human decision.

---

## Slide 10. Anti-Patterns to Avoid

### On-slide bullets

- Over-permissioning: edit: allow for all agents defeats the model
- Mega-skills: one 500-line skill becomes unmaintainable
- Skipping the review gate: /deploy without /review-ml
- Hardcoding environment details in skills
- Skill drift: stale skills give agents outdated rules

### Speaker notes

Every one of these is something we either did ourselves or watched another team run into. I am sharing them because knowing what to avoid ahead of time is genuinely more useful than discovering it the hard way.

Over-permissioning is the most common early mistake. When you are setting things up for the first time, it is tempting to give every agent edit: allow just to get moving quickly. The problem is you have immediately disabled the core safety property of the system. One agent with bad instructions can now modify anything. The rule is simple: read-only is the default. Write access gets granted explicitly, per agent, for a specific reason.

Mega-skills are a trap that feels like good engineering at first. Writing one comprehensive skill that covers EDA, training, and deployment seems efficient. Six months later it is five hundred lines long, half of it is stale, and no one can tell which rules are still valid. One skill per stage. Small, focused, independently updateable. When a pipeline pattern changes, you update one file.

Skipping the review gate is almost always done under time pressure. "This change is small, I'll skip the review this time." The review gate is not there for large changes — automated tests handle the obvious things. It is there for the subtle, ML-specific failures that pass every automated check but break silently in production. Those are exactly the ones that appear in small, "obviously safe" changes.

Hardcoding environment-specific values in skills is a portability problem. The moment a skill references a specific workspace name or storage URI, it stops working for any other team or repository. Skills should reference documentation schemas. Environment values belong in config.

Skill drift is the quiet long-term failure mode. The pipeline evolves, argument signatures change, deployment procedures update — but the skills are not updated alongside them. Agents then follow rules that describe a system that no longer exists. Skills are living documents. They need the same update discipline as the code they describe.

---

## Slide 11. Adoption Path & Summary

### On-slide bullets

- Maturity model: L0 Manual → L4 Adaptive
- This setup operates at L3–L4. Recommended target: L3
- Getting started: 3 steps, ~2.5 hours total
- Strengths: minimum-permission agents, hardcoded ML guardrails, 13 decoupled skills, config-only drop-in
- Next steps: metric threshold gates, expanded autoresearch, post-deploy drift monitoring

### Speaker notes

Let me close with a practical picture of where you might be right now, where this system sits, and how to get from one to the other.

The maturity model has five levels. L0 is fully manual — you run every Azure ML command by hand, write profiling code per engagement, manage deployments without any automated sequence. L1 is assisted — slash commands exist, maybe a general-purpose agent, but nothing is scoped or governed. L2 is orchestrated — multi-agent routing is in place, but there are no enforced guardrails. L3 is governed — the permission intercepts are active, the deployment gates are enforced, the audit trail is complete. L4 is adaptive — an autonomous experiment loop runs overnight and surfaces results for human review.

Most teams using AI tooling today are at L1 or L2. This configuration operates at L3 to L4. For teams moving toward production use, L3 is the right target. The governance layer and audit trail are what make AI-assisted delivery trustworthy enough to show a stakeholder or run in a regulated environment.

Getting to L3 takes less time than you might expect. Step one is about thirty minutes: drop opencode.json and a docs folder into your repository. No source code changes required — the permission model, MCP configuration, formatter rules, all of it is in that one file. Step two is roughly two hours: define your agents and skills. One markdown file per agent, read-only by default, one skill file per workflow stage. Step three is immediate: run /eda or /review-ml and watch what happens. Watch the routing, the skill loading, the audit trail. The system shows its structure clearly from the first run.

The strengths that matter most are the ones that pay off over time. Minimum-permission agents mean any individual failure has a bounded blast radius. Hardcoded ML guardrails apply the same checks regardless of who runs the workflow. Decoupled skills mean domain knowledge stays current without touching agent logic. And a config-only setup means any ML repository can adopt this without a single line of source code change.

Honest remaining work: standardised metric threshold gates in the evaluation phase, expanded autoresearch scope, and closed-loop drift monitoring that feeds back into the experiment cycle after deployment.

---

## Slide 12. Live Demo

### On-slide bullets

- Step 1: /eda — routing to ml-data-analyst, skill load, profile-dataset.py, leakage flags
- Step 2: /train — planner invoked before code, sequential-thinking MCP, Karpathy principles live
- Step 3: /review-ml — isolated read-only reviewer, str_to_bool + leakage + MLflow + YAML sync
- Expected output: dataset-profile.md · experiment-plan.md · structured review report

### Speaker notes

Let me show you the system running. Three commands, and at each step I want you to pay attention not just to what comes out, but to how the system gets there — because the routing, the skill loading, and the permission enforcement are the evidence for everything we have just discussed.

First: /eda on the dataset. Watch the routing — the orchestrator receives the command, identifies exploratory intent, and hands off to the data analyst. Not a general-purpose model, a specific specialist with bounded permissions and a scoped skill. Watch the skill load appear in the action log: ml-eda loads and brings the leakage rules, null thresholds, and offset_date audit criteria with it. Watch profile-dataset.py run under read-only access — no files modified, no side effects. The output is a structured report with leakage flags included automatically, because the skill encodes that as a standard deliverable.

Second: /train. Watch the orchestrator invoke the experiment planner before the code builder is ever engaged. Sequential-thinking MCP activates. The planner works through the problem step by step, applies the four principles, and produces a plan. You can read it, approve it, or push back on it. The code builder does not start until that plan exists.

Third: /review-ml. Watch the reviewer operate in complete isolation — read-only, no bash, no file writes. It runs through its checklist: str_to_bool compliance, temporal leakage guards, MLflow run handling, component YAML synchronisation. Every finding comes back with a file, a line number, the issue, and the fix. CRITICALs show in red and block deployment until resolved.

If the demo environment is not available today, this diagram is the walkthrough — every step maps to a real artifact shown in the previous slide. The system is designed to be readable. The audit trail tells the story even when you are not watching in real time.

---

## Closing. One-Line Takeaway

### On-slide bullets

- Agentic Engineering makes ML workflows faster, safer, and more repeatable — with a config-only setup

### Speaker notes

Here is the thing I want you to take away from this talk.

We are not trying to replace engineers. We are trying to make the structural parts of engineering — the sequencing, the guardrails, the review gates, the audit trail — reliable and automatic. So that engineers can focus on the decisions that genuinely require human judgement: which model architecture fits the problem, what an ambiguous result in the data actually means, whether a metric improvement is significant enough to act on.

Agentic Engineering is a disciplined system. It took us real time to build, and the guardrail design went through several iterations before it was right. But the result is something any ML team, software team, or QA team can pick up, adapt to their domain, and get the safety and repeatability benefits without having to rebuild the infrastructure from scratch.

Six subagents. Thirteen skills. Nine slash commands. One config file. Already running in production.

Thank you.
