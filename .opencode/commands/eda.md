---
description: Run exploratory data analysis on a dataset. Usage: /eda <path>
---

# Perform exploratory data analysis on the dataset at: $ARGUMENTS

Current directory: !`pwd`
Available parquet files: !`find . -name "*.parquet" -not -path "*/mlruns/*" 2>/dev/null | head -20`

Use the `ml-data-analyst` agent and the `profile-dataset` tool to:

1. Load the dataset and report shape, dtypes, memory usage
2. Compute null counts and percentages per column
3. Identify duplicate rows
4. For numeric columns: min, max, mean, median, std, skew, kurtosis
5. For categorical columns: cardinality, top-5 values and frequencies
6. Analyse the target column distribution (class balance or regression distribution)
7. Check for temporal leakage risks — flag any column that could encode future information
8. Identify columns that should be excluded from modelling (IDs, dates used as keys)

Refer to `docs/data-schema.md` for known column definitions and leakage patterns for this repo.

Produce a structured markdown report with actionable findings and recommended next steps.
