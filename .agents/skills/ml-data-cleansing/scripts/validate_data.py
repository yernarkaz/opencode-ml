"""Validate a cleaned dataset before it enters the feature engineering step.

Checks null rates, dtype correctness, duplicate keys, date parse-ability of
offset_date, and required column presence. Returns a JSON validation report.

Usage:
    python validate_data.py --file_path data/clean.parquet --required_cols col1,col2,col3
    python validate_data.py --file_path data/clean.parquet --required_cols id,date,target --key_cols id,date
    python validate_data.py --file_path data/clean.parquet --required_cols id,target --target_col target --target_type binary

Exit codes:
    0  All checks passed
    2  Warnings (high nulls, soft failures) — review recommended
    1  Fatal error (missing required columns, unreadable file)
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
NULL_WARN_THRESHOLD = 0.20  # 20% nulls triggers a warning
NULL_FATAL_THRESHOLD = 0.80  # 80% nulls in a required column is a fatal error


def validate(
    file_path: str,
    required_cols: List[str],
    key_cols: Optional[List[str]],
    target_col: Optional[str],
    target_type: Optional[str],
) -> dict:
    df = (
        pd.read_parquet(file_path)
        if file_path.endswith(".parquet")
        else pd.read_csv(file_path)
    )

    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Any] = {}

    # 1. Required column presence
    missing_cols = [c for c in required_cols if c not in df.columns]
    checks["required_columns"] = {
        "required": required_cols,
        "missing": missing_cols,
        "pass": len(missing_cols) == 0,
    }
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # 2. Null rate per required column
    null_report = {}
    for col in required_cols:
        if col not in df.columns:
            continue
        null_pct = df[col].isna().mean()
        null_report[col] = round(float(null_pct), 4)
        if null_pct >= NULL_FATAL_THRESHOLD:
            errors.append(f"{col}: {null_pct:.0%} nulls — exceeds fatal threshold")
        elif null_pct >= NULL_WARN_THRESHOLD:
            warnings.append(
                f"{col}: {null_pct:.0%} nulls — above 20% warning threshold"
            )
    checks["null_rates"] = null_report

    # 3. Duplicate key check
    if key_cols:
        valid_key_cols = [c for c in key_cols if c in df.columns]
        if valid_key_cols:
            n_dupes = int(df.duplicated(subset=valid_key_cols).sum())
            checks["duplicate_keys"] = {
                "key_cols": valid_key_cols,
                "duplicate_count": n_dupes,
                "pass": n_dupes == 0,
            }
            if n_dupes > 0:
                warnings.append(f"{n_dupes} duplicate rows on key {valid_key_cols}")

    # 4. offset_date parseable as datetime (if present)
    if "offset_date" in df.columns:
        try:
            pd.to_datetime(df["offset_date"], errors="raise")
            checks["offset_date_parseable"] = True
        except Exception as exc:
            checks["offset_date_parseable"] = False
            errors.append(f"offset_date not parseable as datetime: {exc}")

    # 5. Target column type checks
    if target_col and target_col in df.columns:
        if target_type == "binary":
            unique_vals = set(df[target_col].dropna().unique())
            is_binary = unique_vals <= {0, 1}
            checks["target_binary"] = {
                "unique_values": sorted(unique_vals),
                "pass": is_binary,
            }
            if not is_binary:
                errors.append(f"{target_col} has non-binary values: {unique_vals}")
        elif target_type == "non_negative":
            n_neg = int((df[target_col] < 0).sum())
            checks["target_non_negative"] = {
                "negative_count": n_neg,
                "pass": n_neg == 0,
            }
            if n_neg > 0:
                warnings.append(f"{target_col}: {n_neg} negative values — expected ≥ 0")

    return {
        "file": file_path,
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate a cleaned dataset before feature engineering."
    )
    parser.add_argument(
        "--file_path", required=True, help="Path to parquet or CSV file"
    )
    parser.add_argument(
        "--required_cols",
        required=True,
        help="Comma-separated list of required column names",
    )
    parser.add_argument(
        "--key_cols",
        default=None,
        help="Comma-separated composite key columns for duplicate check",
    )
    parser.add_argument(
        "--target_col",
        default=None,
        help="Target column name to validate (optional)",
    )
    parser.add_argument(
        "--target_type",
        default=None,
        choices=["binary", "non_negative"],
        help="Type constraint for target column validation",
    )
    args = parser.parse_args()

    required_cols = [c.strip() for c in args.required_cols.split(",")]
    key_cols = [c.strip() for c in args.key_cols.split(",")] if args.key_cols else None

    try:
        result = validate(
            args.file_path,
            required_cols,
            key_cols,
            args.target_col,
            args.target_type,
        )
        print(json.dumps(result, indent=2))

        if not result["passed"]:
            sys.exit(1)
        if result["warnings"]:
            sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e), "file": args.file_path}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
