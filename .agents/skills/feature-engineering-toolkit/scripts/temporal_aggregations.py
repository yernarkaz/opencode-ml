"""Template for computing temporal rolling aggregations with offset_date respect.

This script demonstrates the correct pattern for computing rolling window features
in Azure ML pipelines. Every aggregation respects the per-row offset_date cutoff
to prevent data leakage.

Usage:
    python temporal_aggregations.py \
        --input_path /path/to/events.parquet \
        --metadata_path /path/to/metadata.parquet \
        --output_path /path/to/temporal_features.parquet \
        --entity_col part_id \
        --date_col event_date \
        --offset_col offset_date \
        --value_col measurement_value \
        --windows 30 90 180
"""

import argparse
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Compute temporal rolling aggregations respecting per-row offset_date."
    )
    parser.add_argument("--input_path", type=str, required=True,
                        help="Path to events parquet file.")
    parser.add_argument("--metadata_path", type=str, required=True,
                        help="Path to metadata parquet file with offset_date per row.")
    parser.add_argument("--output_path", type=str, required=True,
                        help="Path to write output features parquet.")
    parser.add_argument("--entity_col", type=str, default="entity_id",
                        help="Column name for entity identifier.")
    parser.add_argument("--date_col", type=str, default="event_date",
                        help="Column name for event date in events data.")
    parser.add_argument("--offset_col", type=str, default="offset_date",
                        help="Column name for per-row cutoff date in metadata.")
    parser.add_argument("--value_col", type=str, default="value",
                        help="Column name for numeric value to aggregate.")
    parser.add_argument("--windows", type=int, nargs="+", default=[30, 90, 180],
                        help="Rolling window sizes in days.")
    return parser.parse_args()


def compute_rolling_features(events: pd.DataFrame, metadata: pd.DataFrame,
                              entity_col: str, date_col: str,
                              offset_col: str, value_col: str,
                              windows: list[int]) -> pd.DataFrame:
    """Compute rolling aggregations for each entity, respecting per-row offset_date.

    For each row in metadata, this function:
    1. Filters events to those strictly before the row's offset_date
    2. Computes rolling statistics for each window size
    3. Returns a dataframe of features aligned to metadata rows

    Args:
        events: Event-level data with entity, date, and value columns.
        metadata: Metadata with entity and per-row offset_date.
        entity_col: Entity identifier column name.
        date_col: Event date column name.
        offset_col: Per-row cutoff date column name.
        value_col: Numeric value column to aggregate.
        windows: List of rolling window sizes in days.

    Returns:
        Dataframe with rolling feature columns, indexed by metadata index.
    """
    # Pre-sort events for efficient filtering
    events_sorted = events.sort_values([entity_col, date_col]).reset_index(drop=True)
    events_by_entity = events_sorted.groupby(entity_col)

    all_features = []

    for idx, row in metadata.iterrows():
        entity_id = row[entity_col]
        offset_date = row[offset_col]

        # Get events for this entity
        if entity_id not in events_by_entity.groups:
            all_features.append(_empty_features(value_col, windows))
            continue

        entity_events = events_by_entity.get_group(entity_id)

        # STRICT less-than: only events before offset_date
        history = entity_events[entity_events[date_col] < offset_date]

        if len(history) == 0:
            all_features.append(_empty_features(value_col, windows))
            continue

        features = {"entity_id": entity_id}

        for w in windows:
            window_start = offset_date - pd.Timedelta(days=w)
            window_data = history[(history[date_col] >= window_start)][value_col]

            features[f"{value_col}_mean_{w}d"] = window_data.mean()
            features[f"{value_col}_std_{w}d"] = window_data.std()
            features[f"{value_col}_count_{w}d"] = len(window_data)
            features[f"{value_col}_sum_{w}d"] = window_data.sum()
            features[f"{value_col}_max_{w}d"] = window_data.max()
            features[f"{value_col}_min_{w}d"] = window_data.min()

        all_features.append(features)

    return pd.DataFrame(all_features, index=metadata.index)


def _empty_features(value_col: str, windows: list[int]) -> dict:
    """Return a dict of NaN features for entities with no history.

    Args:
        value_col: Value column name for feature naming.
        windows: List of window sizes.

    Returns:
        Dict with all feature keys set to NaN.
    """
    features = {}
    for w in windows:
        for suffix in ["mean", "std", "count", "sum", "max", "min"]:
            features[f"{value_col}_{suffix}_{w}d"] = np.nan
    return features


def compute_lag_features(events: pd.DataFrame, metadata: pd.DataFrame,
                          entity_col: str, date_col: str,
                          offset_col: str, value_col: str,
                          lags: list[int]) -> pd.DataFrame:
    """Compute lag features from historical data before offset_date.

    Args:
        events: Event-level data.
        metadata: Metadata with per-row offset_date.
        entity_col: Entity identifier column.
        date_col: Event date column.
        offset_col: Per-row cutoff date column.
        value_col: Numeric value column.
        lags: List of lag periods in months.

    Returns:
        Dataframe with lag feature columns.
    """
    events_sorted = events.sort_values([entity_col, date_col]).reset_index(drop=True)
    events_by_entity = events_sorted.groupby(entity_col)

    all_features = []

    for _, row in metadata.iterrows():
        entity_id = row[entity_col]
        offset_date = row[offset_col]

        if entity_id not in events_by_entity.groups:
            all_features.append(_empty_lag_features(value_col, lags))
            continue

        entity_events = events_by_entity.get_group(entity_id)
        history = entity_events[entity_events[date_col] < offset_date]

        if len(history) == 0:
            all_features.append(_empty_lag_features(value_col, lags))
            continue

        features = {"entity_id": entity_id}
        for lag in lags:
            lag_cutoff = offset_date - pd.DateOffset(months=lag)
            lag_data = history[history[date_col] >= lag_cutoff][value_col]
            features[f"{value_col}_lag_{lag}m"] = lag_data.mean()

        all_features.append(features)

    return pd.DataFrame(all_features, index=metadata.index)


def _empty_lag_features(value_col: str, lags: list[int]) -> dict:
    """Return a dict of NaN lag features.

    Args:
        value_col: Value column name.
        lags: List of lag periods.

    Returns:
        Dict with all lag feature keys set to NaN.
    """
    return {f"{value_col}_lag_{lag}m": np.nan for lag in lags}


def main() -> None:
    """Main entry point for temporal aggregation computation."""
    args = parse_args()

    logger.info("Loading events from %s", args.input_path)
    events = pd.read_parquet(args.input_path)

    logger.info("Loading metadata from %s", args.metadata_path)
    metadata = pd.read_parquet(args.metadata_path)

    # Ensure date columns are datetime
    events[args.date_col] = pd.to_datetime(events[args.date_col], errors="coerce")
    metadata[args.offset_col] = pd.to_datetime(metadata[args.offset_col], errors="coerce")

    # Drop rows with invalid dates
    na_dates = events[args.date_col].isna().sum()
    na_offsets = metadata[args.offset_col].isna().sum()
    if na_dates > 0:
        logger.warning("Dropping %d events with invalid dates", na_dates)
        events = events.dropna(subset=[args.date_col])
    if na_offsets > 0:
        logger.warning("Dropping %d metadata rows with invalid offset dates", na_offsets)
        metadata = metadata.dropna(subset=[args.offset_col])

    # Compute rolling features
    logger.info("Computing rolling features with windows %s", args.windows)
    rolling_features = compute_rolling_features(
        events=events,
        metadata=metadata,
        entity_col=args.entity_col,
        date_col=args.date_col,
        offset_col=args.offset_col,
        value_col=args.value_col,
        windows=args.windows,
    )

    # Compute lag features
    logger.info("Computing lag features")
    lag_features = compute_lag_features(
        events=events,
        metadata=metadata,
        entity_col=args.entity_col,
        date_col=args.date_col,
        offset_col=args.offset_col,
        value_col=args.value_col,
        lags=[1, 3, 6],
    )

    # Combine features
    combined = pd.concat([rolling_features, lag_features], axis=1)

    # Merge back to metadata
    output = metadata.merge(combined, left_index=True, right_index=True, how="left")

    # Save output
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(str(output_path), index=False)
    logger.info("Saved %d features to %s", len(output.columns), args.output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
