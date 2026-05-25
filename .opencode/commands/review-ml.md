---
description: Review ML pipeline code changes for correctness, leakage, and style.
subtask: true
---

# Review the following ML pipeline code changes

Changed files: !`git diff --name-only HEAD 2>/dev/null || git status --short`
Diff: !`git diff HEAD 2>/dev/null | head -500`

Use the `ml-code-reviewer` agent to perform a structured review covering:

1. **Temporal leakage** — all feature aggregations filter on `< offset_date`
2. **Feature system correctness** — training feature set does not include inference-only features (unavailable for new records at training time)
3. **Log transform correctness** — `log1p` before training, `expm1` after prediction, caps applied
4. **AML component alignment** — every ArgumentParser arg has a matching component YAML input
5. **MLflow run management** — no unconditional `mlflow.start_run()` in Azure ML environment
6. **Style compliance** — type annotations, Google docstrings, f-strings, import order, no bare `except`
7. **Test coverage** — are new functions covered by unit tests?

Output findings as:
`[SEVERITY] file:line — description — suggested fix`

Severity levels: CRITICAL | WARNING | SUGGESTION

End with: **Review result: PASS / NEEDS CHANGES**

This review runs in an isolated subtask — findings are summarised back to the main session.
