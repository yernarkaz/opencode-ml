# Contributing to opencode-ml

This guide covers how to extend the OpenCode ML configuration repo.

---

## Adding a new skill

Skills are on-demand — loaded explicitly by the agent when the task matches the skill description.

### Directory structure

```
.agents/skills/<skill-name>/
  SKILL.md              # Instructions injected into agent context
  evals/
    evals.json          # Evaluation cases for the skill
  scripts/              # Optional: helper scripts referenced by the skill
```

### SKILL.md format

```markdown
# <Skill Name>

<One-sentence description of what the skill does and when to use it.>

## Trigger conditions
- "trigger phrase 1"
- "trigger phrase 2"

## Workflow
1. Step one
2. Step two

## Reference
- Link to relevant docs or conventions
```

### evals.json format

```json
{
  "skill": "<skill-name>",
  "evals": [
    {
      "id": "eval-001",
      "prompt": "Sample user prompt that should trigger this skill",
      "expected_behavior": "Description of what the agent should do"
    }
  ]
}
```

### Registration

Skills are auto-discovered from `.agents/skills/` — no manual registration needed. The skill name is derived from the directory name.

---

## Adding a new command

Commands live in `.opencode/commands/` and are invoked with `/command-name`.

### Command file format

```markdown
# /command-name

<Description of what the command does.>

subtask: true

<Instructions for the agent. Use backtick-quoted shell commands to inject live output:>
Run: `git status`
```

### Key conventions

- Use `subtask: true` to isolate the command in a separate agent session
- Shell commands in backticks are executed and their output injected into the prompt
- Keep commands focused on a single workflow step
- Command names use kebab-case

---

## Adding a new agent

Agents live in `.opencode/agents/` and define subagent behavior.

### Agent definition format

```markdown
# <Agent Name>

<Description of the agent's role.>

## Permissions
- edit: allow | deny
- bash: allow | deny
- read: allow

## Instructions
<Step-by-step instructions for the agent.>
```

### Permission model

- **Read-only agents** (reviewers, analysts): `edit: deny`, `bash: deny`
- **Builder agents** (code writers, pipeline builders): `edit: allow`, `bash: allow`
- Never grant a subagent broader permissions than the parent session

---

## Adding a new tool

Tools consist of a TypeScript registration and an optional Python backing script.

### Directory structure

```
.opencode/tools/
  <tool-name>.ts          # TypeScript registration + UI
  <tool-name>.py          # Optional: Python backing script
```

### Registration

The TypeScript file defines the tool schema, parameters, and execution logic. Reference the Python script path if the tool delegates to a backing script.

---

## Adding a new use-case

Use the `/new-usecase` command to scaffold a new ML use-case directory with:
- Data schema template
- Experiment conventions template
- Pipeline component stubs
- Agent configuration

---

## Git workflow

### Branching

- **`develop`** — active development branch (default)
- **`main`** — stable releases, tagged versions

### PR process

1. Create a feature branch from `develop`
2. Make changes and commit
3. Open a PR targeting `develop`
4. Request review using `/review-ml`
5. Merge after approval

### Tagging

```bash
git checkout main
git tag -a v<major>.<minor>.<patch> -m "vX.Y.Z: <description>"
git push origin main --tags
```

---

## Testing changes

### Verify evals.json

```bash
python -c "import json; json.load(open('.agents/skills/<skill>/evals/evals.json'))"
```

### Run code review

Use `/review-ml` to validate changes against the repo conventions.

### Verify opencode.json

```bash
python -c "import json; json.load(open('opencode.json'))"
```

### Check skill loading

Start a new session and verify the skill appears in the available_skills list.
