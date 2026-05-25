"""Audit a feature dataset for temporal leakage relative to offset_date.

For each numeric feature, checks whether its value could have been computed
using data from after offset_date — a common source of leakage in ML pipelines
that use a per-row temporal cutoff.

Specifically checks:
  1. That offset_date is present and parseable.
  2. That no feature column name matches a known post-cutoff pattern
     (e.g. columns containing 'future', 'next', 'post', 'after').
  3. That no known inference-only features appear in the training feature set.
     Pass these via --inference_only_cols if applicable to your use-case.
  4. Reports per-column null rate broken down by whether the row is in
     the future relative to a reference date — a spike in nulls post-cutoff
     often indicates a leaking join.

Usage:
    python audit_leakage.py --file_path features.parquet
    python audit_leakage.py --file_path features.parquet --reference_date 2024-01-01
    python audit_leakage.py --file_path features.parquet \\
        --inference_only_cols measurement_count,measurement_cpk_mean \\
        --reference_date 2024-01-01

Exit codes:
    0  No leakage detected
    2  Potential leakage warnings — manual review required
    1  Fatal error (missing offset_date, unreadable file)
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import pandas as pd


# Patterns in column names that suggest future-leaking features
SUSPICIOUS_PATTERNS = ["future", "next_", "post_", "after_", "_fwd", "_lead"]


def audit(
    file_path: str,
    inference_only_cols: Optional[List[str]],
    reference_date: Optional[str],
) -> dict:
    df = (
        pd.read_parquet(file_path)
        if file_path.endswith(".parquet")
        else pd.read_csv(file_path)
    )

    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Any] = {}

    # 1. offset_date presence and parseability
    if "offset_date" not in df.columns:
        errors.append("offset_date column is missing — cannot audit temporal leakage")
        return {
            "file": file_path,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "passed": False,
        }

    try:
        df["offset_date"] = pd.to_datetime(df["offset_date"])
        checks["offset_date_parseable"] = True
    except Exception as exc:
        errors.append(f"offset_date not parseable: {exc}")
        return {
            "file": file_path,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "passed": False,
        }

    # 2. Suspicious column name patterns
    suspicious_cols = [
        col
        for col in df.columns
        if any(pat in col.lower() for pat in SUSPICIOUS_PATTERNS)
    ]
    checks["suspicious_column_names"] = {
        "patterns_checked": SUSPICIOUS_PATTERNS,
        "flagged_columns": suspicious_cols,
        "pass": len(suspicious_cols) == 0,
    }
    for col in suspicious_cols:
        warnings.append(
            f"Column '{col}' matches suspicious pattern — verify it uses only data < offset_date"
        )

    # 3. Inference-only feature check (if provided)
    if inference_only_cols:
        leaked_inference_cols = [c for c in inference_only_cols if c in df.columns]
        checks["inference_only_features_in_training"] = {
            "forbidden_cols": inference_only_cols,
            "found_in_dataset": leaked_inference_cols,
            "pass": len(leaked_inference_cols) == 0,
        }
        for col in leaked_inference_cols:
            warnings.append(
                f"'{col}' is an inference-only feature — unavailable for new records at training time. "
                "Remove it from the training feature set."
            )

    # 4. Null rate spike analysis relative to reference_date
    if reference_date:
        ref_ts = pd.Timestamp(reference_date)
        pre = df[df["offset_date"] <= ref_ts]
        post = df[df["offset_date"] > ref_ts]

        null_spike_report = {}
        for col in df.select_dtypes(include="number").columns:
            if col == "offset_date":
                continue
            pre_null = pre[col].isna().mean() if len(pre) > 0 else 0.0
            post_null = post[col].isna().mean() if len(post) > 0 else 0.0
            spike = post_null - pre_null
            null_spike_report[col] = {
                "pre_null_pct": round(float(pre_null) * 100, 2),
                "post_null_pct": round(float(post_null) * 100, 2),
                "spike_pct": round(float(spike) * 100, 2),
            }
            if spike > 0.15:  # 15 percentage point increase
                warnings.append(
                    f"'{col}': null rate spikes {spike:.0%} after {reference_date} — "
                    "may indicate a leaking join producing nulls for future rows"
                )

        checks["null_spike_by_reference_date"] = {
            "reference_date": reference_date,
            "pre_count": len(pre),
            "post_count": len(post),
            "per_column": null_spike_report,
        }

    return {
        "file": file_path,
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "offset_date_range": {
            "min": str(df["offset_date"].min()),
            "max": str(df["offset_date"].max()),
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
        "warning_count": len(warnings),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit feature dataset for temporal leakage relative to offset_date."
    )
    parser.add_argument(
        "--file_path", required=True, help="Path to parquet or CSV file"
    )
    parser.add_argument(
        "--inference_only_cols",
        default=None,
        help="Comma-separated column names that are only available at inference time "
        "(not for new records at training time)",
    )
    parser.add_argument(
        "--reference_date",
        default=None,
        help="Optional date (YYYY-MM-DD) to split pre/post for null-spike analysis",
    )
    args = parser.parse_args()

    inference_only_cols = (
        [c.strip() for c in args.inference_only_cols.split(",")]
        if args.inference_only_cols
        else None
    )

    try:
        result = audit(args.file_path, inference_only_cols, args.reference_date)
        print(json.dumps(result, indent=2, default=str))

        if not result["passed"]:
            sys.exit(1)
        if result["warning_count"] > 0:
            sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e), "file": args.file_path}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
