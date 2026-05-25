---
description: Scaffold a new ML use-case into this config repo. Usage: /new-usecase <RepoName> <problem_type> <primary_metric>
---

# Scaffold a new ML use-case: $ARGUMENTS

Current config repo: !`pwd`
Existing use-cases in data-schema.md: !`grep "^## " docs/data-schema.md 2>/dev/null`
Existing program files: !`ls docs/program-*.md 2>/dev/null`

Parse `$ARGUMENTS` as: `<RepoName> <problem_type> <primary_metric>`

- `RepoName` — repo name, e.g. `MyRepoSpendForecast`
- `problem_type` — one of: `binary_classification`, `regression`, `multi_target_regression`
- `primary_metric` — metric used for acceptance gate, e.g. `roc_auc`, `r2`, `mape`

If any argument is missing, ask the user before proceeding.

---

## Steps to execute

### 1. Add a new section to `docs/data-schema.md`

Append a new section following the existing pattern:

```markdown
---

## <RepoName> — <short description>

**Problem**: <problem_type in plain English>

### Key columns

| Column | Type | Description |
|---|---|---|
| `<id_column>` | str | Primary identifier |
| `<target_column>` | <type> | **Target** — <description> |

### Key patterns

- <fill in repo-specific patterns after onboarding>
```

Use `<FILL IN>` for any field you do not yet know. Do not invent values.

### 2. Create `docs/program-<reponame_lowercase>.md`

Use this template:

```markdown
# Autoresearch Program — <RepoName>

## Objective

Improve `<primary_metric>` on the `<RepoName>` model.

## Baseline (fill in after first training run)

| Metric | Value |
|---|---|
| `<primary_metric>` | <FILL IN> |

## Acceptance gate

| Condition | Threshold |
|---|---|
| `<primary_metric>` | > <FILL IN> |

## Hypotheses (seed list)

1. Tune LightGBM `num_leaves` and `min_child_samples`
2. Add CatBoost as an ensemble member
3. Engineer lag features from historical supplier data

## Keep/discard rules

- Keep: `<primary_metric>` improves by > 0.005 on held-out test set
- Discard: any run where test metric is worse than baseline

## Notes

- Problem type: <problem_type>
- Repo: <RepoName>
- Created: <today's date>
```

### 3. Print an onboarding checklist

After creating the files, print this checklist for the user:

```
## Onboarding checklist for <RepoName>

### In this config repo (done automatically above)
- [x] docs/data-schema.md — new section added
- [x] docs/program-<reponame>.md — created with <FILL IN> baselines

### In the target repo <RepoName> — do these manually
- [ ] Copy docs/program-<reponame>.md to the repo root as program.md
- [ ] Fill in <FILL IN> baseline metric values after the first training run
- [ ] Add the four pipeline scripts (preprocess_clean_data, engineer_features, train_model, inference_model)
- [ ] Add AML component YAMLs in aml/pipeline/components/
- [ ] Add str_to_bool to utils/arg_parsing.py
- [ ] Add ArgumentParserMixin for shared Azure arg groups
- [ ] Configure MLflow experiment name in docs/experiment-conventions.md: <reponame_lowercase>-training

### Refer to
- docs/data-schema.md — patterns from existing use-cases to copy
- docs/experiment-conventions.md — MLflow and deployment conventions (if populated)
```
