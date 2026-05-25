"""Profile a parquet or CSV dataset and return structured statistics as JSON.

PEP 723 inline dependencies — run with: uv run profile-dataset.py --file_path <path>
"""

# /// script
# dependencies = [
#   "pandas>=2.0",
#   "pyarrow>=14.0",
#   "scipy>=1.11",
# ]
# ///

from __future__ import annotations

import argparse
import json
import logging
import sys

logger = logging.getLogger(__name__)


def _load_file(file_path: str, sample_rows: int | None):
    import pandas as pd

    if file_path.endswith(".parquet"):
        df = pd.read_parquet(file_path)
    elif file_path.endswith((".csv", ".tsv")):
        sep = "\t" if file_path.endswith(".tsv") else ","
        df = pd.read_csv(file_path, sep=sep)
    else:
        raise ValueError(
            f"Unsupported file type: {file_path}. Expected .parquet, .csv, or .tsv"
        )

    if sample_rows and len(df) > sample_rows:
        df = df.sample(n=sample_rows, random_state=42)
        logger.warning("Sampled %d rows (file has more)", sample_rows)

    return df


def profile(file_path: str, target_col: str | None, sample_rows: int | None) -> dict:
    import numpy as np
    import pandas as pd
    from scipy import stats as sp_stats

    df = _load_file(file_path, sample_rows)

    result: dict = {
        "file": file_path,
        "shape": {"rows": len(df), "cols": len(df.columns)},
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1_048_576, 2),
        "columns": {},
        "duplicate_rows": int(df.duplicated().sum()),
        "warnings": [],
    }

    for col in df.columns:
        s = df[col]
        null_count = int(s.isna().sum())
        null_pct = round(null_count / len(df) * 100, 2)
        info: dict = {
            "dtype": str(s.dtype),
            "null_count": null_count,
            "null_pct": null_pct,
        }

        if null_pct > 20:
            result["warnings"].append(f"{col}: high null rate ({null_pct}%)")

        if pd.api.types.is_numeric_dtype(s):
            valid = s.dropna()
            skew_val = (
                round(float(sp_stats.skew(valid.to_numpy())), 4)
                if len(valid) > 2
                else None
            )
            info.update(
                {
                    "type": "numeric",
                    "min": round(float(valid.min()), 4) if len(valid) else None,
                    "max": round(float(valid.max()), 4) if len(valid) else None,
                    "mean": round(float(valid.mean()), 4) if len(valid) else None,
                    "median": round(float(valid.median()), 4) if len(valid) else None,
                    "std": round(float(valid.std()), 4) if len(valid) else None,
                    "skew": skew_val,
                }
            )
            if skew_val and abs(skew_val) > 2:
                result["warnings"].append(
                    f"{col}: high skew ({skew_val:.2f}) — consider log transform"
                )
        else:
            cardinality = int(s.nunique())
            top5 = s.value_counts().head(5).to_dict()
            info.update(
                {
                    "type": "categorical",
                    "cardinality": cardinality,
                    "top5": {str(k): int(v) for k, v in top5.items()},
                }
            )

        result["columns"][col] = info

    if target_col and target_col in df.columns:
        t = df[target_col].dropna()
        if pd.api.types.is_numeric_dtype(t) and t.nunique() == 2:
            pos_rate = round(float(t.mean()) * 100, 2)
            result["target_analysis"] = {
                "col": target_col,
                "type": "binary_classification",
                "positive_rate_pct": pos_rate,
            }
            if not (5 <= pos_rate <= 15):
                result["warnings"].append(
                    f"Target {target_col}: positive rate {pos_rate}% is outside"
                    " expected 5-15% range — verify against your use-case baseline"
                )
        elif pd.api.types.is_numeric_dtype(t):
            nonneg = np.asarray(t[t >= 0])
            log_skew = (
                round(float(sp_stats.skew(np.log1p(nonneg))), 4)
                if len(nonneg) > 2
                else None
            )
            result["target_analysis"] = {
                "col": target_col,
                "type": "regression",
                "min": round(float(t.min()), 4),
                "max": round(float(t.max()), 4),
                "mean": round(float(t.mean()), 4),
                "log1p_skew": log_skew,
            }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile a parquet or CSV dataset and return structured JSON stats.",
    )
    parser.add_argument(
        "--file_path", required=True, help="Path to parquet, CSV, or TSV file"
    )
    parser.add_argument(
        "--target_col",
        default=None,
        help="Target column name for distribution analysis",
    )
    parser.add_argument(
        "--sample_rows",
        type=int,
        default=None,
        help="Sample N rows for large files (default: all rows)",
    )
    args = parser.parse_args()

    try:
        result = profile(args.file_path, args.target_col, args.sample_rows)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e), "file": args.file_path}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
