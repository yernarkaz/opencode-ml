"""Compute standard evaluation metrics for ML model outputs.

Supports three problem types:
  - binary:       Binary classification (AUC, avg precision, Brier score)
  - regression:   Single-target regression (MAE, R², MAPE)
  - multi_target: Multi-target regression (per-target MAE, R², MAPE)

Usage:
    python compute_metrics.py --problem_type binary \\
        --pred_path predictions.parquet --target_col label --pred_col y_score

    python compute_metrics.py --problem_type regression \\
        --pred_path predictions.parquet --target_col weight --pred_col y_pred

    python compute_metrics.py --problem_type multi_target \\
        --pred_path predictions.parquet \\
        --target_cols target_a,target_b,target_c \\
        --pred_suffix _pred

Outputs JSON with all relevant metrics to stdout.
Non-zero exit (2) if acceptance gate thresholds are provided and not met.

Gate thresholds are optional and passed as:
    --gate_min_auc 0.70 --gate_min_ap 0.30    (binary)
    --gate_min_r2 0.60                          (regression / multi_target)
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE ignoring zero-valued actuals to avoid division by zero."""
    mask = y_true > 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return float("nan")
    return float(1 - ss_res / ss_tot)


def _mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def _clip_preds(y_pred: np.ndarray) -> np.ndarray:
    """Clip negative regression predictions to a small positive value."""
    return np.where(y_pred < 0, 0.00001, y_pred)


# ---------------------------------------------------------------------------
# Per-problem-type metric functions
# ---------------------------------------------------------------------------


def compute_binary(
    df: pd.DataFrame,
    target_col: str,
    pred_col: str,
    gate_min_auc: Optional[float],
    gate_min_ap: Optional[float],
) -> dict:
    from sklearn.metrics import (
        average_precision_score,
        brier_score_loss,
        roc_auc_score,
    )

    y_true = df[target_col].to_numpy()
    y_score = df[pred_col].to_numpy()

    ap = float(average_precision_score(y_true, y_score))
    auc = float(roc_auc_score(y_true, y_score))
    brier = float(brier_score_loss(y_true, y_score))
    positive_rate = float(y_true.mean())

    gate_failures: List[str] = []
    if gate_min_auc is not None and auc < gate_min_auc:
        gate_failures.append(f"roc_auc {auc:.4f} < threshold {gate_min_auc}")
    if gate_min_ap is not None and ap < gate_min_ap:
        gate_failures.append(
            f"avg_average_precision {ap:.4f} < threshold {gate_min_ap}"
        )

    return {
        "problem_type": "binary",
        "avg_average_precision": round(ap, 4),
        "roc_auc": round(auc, 4),
        "brier_score": round(brier, 4),
        "positive_rate": round(positive_rate, 4),
        "n_samples": int(len(y_true)),
        "gate_pass": len(gate_failures) == 0,
        "gate_failures": gate_failures if gate_failures else None,
    }


def compute_regression(
    df: pd.DataFrame,
    target_col: str,
    pred_col: str,
    gate_min_r2: Optional[float],
) -> dict:
    # Predictions must already be on original scale (post-expm1 if log-transformed)
    y_true = df[target_col].to_numpy()
    y_pred = _clip_preds(df[pred_col].to_numpy())

    mae = _mae(y_true, y_pred)
    r2 = _r2(y_true, y_pred)
    mape = _safe_mape(y_true, y_pred)

    gate_failures: List[str] = []
    if gate_min_r2 is not None and r2 < gate_min_r2:
        gate_failures.append(f"test_r2 {r2:.4f} < threshold {gate_min_r2}")

    return {
        "problem_type": "regression",
        "test_mae": round(mae, 4),
        "test_r2": round(r2, 4),
        "test_mape_pct": round(mape, 2) if not np.isnan(mape) else None,
        "n_samples": int(len(y_true)),
        "gate_pass": len(gate_failures) == 0,
        "gate_failures": gate_failures if gate_failures else None,
    }


def compute_multi_target(
    df: pd.DataFrame,
    target_cols: List[str],
    pred_suffix: str,
    gate_min_r2: Optional[float],
) -> dict:
    per_target: Dict[str, Any] = {}
    gate_failures: List[str] = []

    for col in target_cols:
        pred_col = f"{col}{pred_suffix}"
        if col not in df.columns or pred_col not in df.columns:
            per_target[col] = {"error": f"Missing column {col!r} or {pred_col!r}"}
            continue

        y_true = df[col].to_numpy()
        y_pred = _clip_preds(df[pred_col].to_numpy())

        r2 = _r2(y_true, y_pred)
        mae = _mae(y_true, y_pred)
        mape = _safe_mape(y_true, y_pred)

        per_target[col] = {
            "r2": round(r2, 4),
            "mae": round(mae, 4),
            "mape_pct": round(mape, 2) if not np.isnan(mape) else None,
        }

        if gate_min_r2 is not None and r2 < gate_min_r2:
            gate_failures.append(f"{col}: r2={r2:.4f} < {gate_min_r2}")

    r2_values = [v["r2"] for v in per_target.values() if "r2" in v]
    worst_r2 = round(min(r2_values), 4) if r2_values else None

    return {
        "problem_type": "multi_target",
        "worst_target_r2": worst_r2,
        "per_target": per_target,
        "n_samples": len(df),
        "gate_pass": len(gate_failures) == 0,
        "gate_failures": gate_failures if gate_failures else None,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute evaluation metrics for ML model predictions."
    )
    parser.add_argument(
        "--problem_type",
        required=True,
        choices=["binary", "regression", "multi_target"],
        help="Problem type determines which metrics are computed",
    )
    parser.add_argument(
        "--pred_path",
        required=True,
        help="Path to parquet file with actuals and predictions",
    )
    parser.add_argument(
        "--target_col",
        default=None,
        help="Actual target column name (binary, regression)",
    )
    parser.add_argument(
        "--target_cols",
        default=None,
        help="Comma-separated target column names (multi_target)",
    )
    parser.add_argument(
        "--pred_col",
        default="y_pred",
        help="Prediction column name for binary/regression (default: y_pred)",
    )
    parser.add_argument(
        "--pred_suffix",
        default="_pred",
        help="Suffix appended to target col names to form pred col names for multi_target (default: _pred)",
    )
    parser.add_argument("--gate_min_r2", type=float, default=None)
    parser.add_argument("--gate_min_auc", type=float, default=None)
    parser.add_argument("--gate_min_ap", type=float, default=None)
    args = parser.parse_args()

    try:
        df = pd.read_parquet(args.pred_path)

        if args.problem_type == "binary":
            if not args.target_col:
                raise ValueError("--target_col required for binary")
            result = compute_binary(
                df, args.target_col, args.pred_col, args.gate_min_auc, args.gate_min_ap
            )
        elif args.problem_type == "regression":
            if not args.target_col:
                raise ValueError("--target_col required for regression")
            result = compute_regression(
                df, args.target_col, args.pred_col, args.gate_min_r2
            )
        else:
            if not args.target_cols:
                raise ValueError("--target_cols required for multi_target")
            target_cols = [c.strip() for c in args.target_cols.split(",")]
            result = compute_multi_target(
                df, target_cols, args.pred_suffix, args.gate_min_r2
            )

        print(json.dumps(result, indent=2))

        if not result.get("gate_pass", True):
            sys.exit(2)
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
