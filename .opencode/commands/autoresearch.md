---
description: Launch an autonomous ML experiment loop against a program.md research spec. Usage: /autoresearch [mode=local|aml]
---

# Autoresearch — autonomous experiment loop

Current repo: !`pwd`
Git branch: !`git branch --show-current 2>/dev/null`
Python: !`python --version 2>/dev/null`
program.md exists: !`[ -f program.md ] && echo "YES — ready" || echo "NO — create program.md before running"`
Current baseline (from program.md): !`grep -A1 '## Baseline' program.md 2>/dev/null | tail -1 || echo "not found"`
results.tsv iterations so far: !`[ -f results.tsv ] && echo "$(wc -l < results.tsv) rows" || echo "no results.tsv yet (will be created)"`
Open hypotheses: !`grep -A20 '## Open hypotheses' program.md 2>/dev/null | grep '^[0-9]' | head -5 || echo "not found"`

---

Run mode requested: $ARGUMENTS

## Before starting

1. If `program.md` does not exist in this repo, stop and tell the user to create it from the template in `docs/autoresearch-template.md` (or copy from another repo).
2. Confirm the mode:
   - **Mode A (local)** — fast iteration (~5-10 min/run), no AML cost, NEVER stops until interrupted
   - **Mode B (AML)** — full pipeline on Azure ML compute, hard cap of 10 jobs per session
   - If `$ARGUMENTS` is empty, ask: "Mode A (local, unlimited) or Mode B (AML, capped at 10 jobs)?"
3. Confirm the primary metric and baseline from `program.md`.
4. Create the autoresearch git branch (done automatically by the agent).

Hand off to `@ml-autoresearch` with the confirmed mode and repo context.
