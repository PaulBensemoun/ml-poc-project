"""Session parser for Coveo SIGIR eCom 2021 browsing events.

Loads raw browsing_train.csv, normalizes columns, sorts events by session and
timestamp, and exposes utility functions that the rest of the v2 pipeline
(splitting.py, features.py, candidates.py, app) can consume.

Usage (quick sample test):
    python sessionize.py --max-rows 500000 --save
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd

from config import BROWSING_RAW, COVEO_PROCESSED_DIR

# ------------------------------------------------------------------- paths ---

PROCESSED_DIR = COVEO_PROCESSED_DIR

# ----------------------------------------------------------------- columns ---

BROWSING_COLS = [
    "session_id_hash",
    "server_timestamp_epoch_ms",
    "event_type",
    "product_action",
    "product_sku_hash",
    "hashed_url",
]

PRODUCT_ACTIONS: frozenset[str] = frozenset({"detail", "add", "remove", "purchase"})

# event_type values observed in the dataset
EVENT_TYPE_PAGEVIEW = "pageview"
EVENT_TYPE_PRODUCT = "event_product"


# ----------------------------------------------------------------- helpers ---

def _read_csv_header(path: Path) -> list[str]:
    """Return column names from the first row of a CSV without loading the file."""
    with path.open(encoding="utf-8", errors="replace") as fh:
        header = fh.readline().rstrip("\n").split(",")
    return [col.strip().strip('"') for col in header]


# ----------------------------------------------------------------- loading ---

def load_browsing_events(
    path: Path = BROWSING_RAW,
    *,
    max_rows: int | None = None,
    sample_sessions: int | None = None,
    seed: int = 42,
) -> pd.DataFrame:
    """Load and normalize browsing events from the raw CSV.

    Parameters
    ----------
    path:
        Path to browsing_train.csv.
    max_rows:
        If set, reads only the first N rows (fast for local iteration).
        Applied before session sampling.
    sample_sessions:
        If set, keeps only a random subset of unique sessions after loading,
        retaining all their events.  Applied after max_rows.
    seed:
        Random seed for reproducible session sampling.

    Returns
    -------
    pd.DataFrame
        Columns: session_id_hash, server_timestamp_epoch_ms, event_type,
        product_action, product_sku_hash, hashed_url.
        Sorted by (session_id_hash, server_timestamp_epoch_ms).
    """
    available = _read_csv_header(path)
    usecols = [c for c in BROWSING_COLS if c in available]

    df = pd.read_csv(
        path,
        usecols=usecols,
        nrows=max_rows,
        dtype=str,
        encoding="utf-8",
        on_bad_lines="skip",
    )

    # Ensure all expected columns exist (fill missing ones with empty string)
    for col in BROWSING_COLS:
        if col not in df.columns:
            df[col] = ""

    # Normalize string fields
    str_cols = [
        "session_id_hash",
        "event_type",
        "product_action",
        "product_sku_hash",
        "hashed_url",
    ]
    for col in str_cols:
        df[col] = df[col].fillna("").str.strip()

    # Parse timestamp to nullable integer
    df["server_timestamp_epoch_ms"] = pd.to_numeric(
        df["server_timestamp_epoch_ms"], errors="coerce"
    ).astype("Int64")

    # Optionally restrict to a random subset of sessions
    if sample_sessions is not None:
        unique_sessions = df.loc[df["session_id_hash"] != "", "session_id_hash"].unique()
        if len(unique_sessions) > sample_sessions:
            rng = np.random.RandomState(seed)
            chosen = rng.choice(unique_sessions, size=sample_sessions, replace=False)
            df = df[df["session_id_hash"].isin(chosen)].copy()

    # Sort by session then chronological order
    df = df.sort_values(
        ["session_id_hash", "server_timestamp_epoch_ms"],
        na_position="last",
    ).reset_index(drop=True)

    return df


def load_session_sample(path: Path = PROCESSED_DIR / "session_sample.parquet") -> pd.DataFrame:
    """Load a previously saved session sample parquet."""
    return pd.read_parquet(path)


# --------------------------------------------------------------- sessions ---

def build_session_index(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build a mapping from session_id_hash to its sorted events DataFrame.

    Parameters
    ----------
    events:
        Output of :func:`load_browsing_events`.

    Returns
    -------
    dict[str, pd.DataFrame]
        Each value is already sorted by timestamp (guaranteed by the loader).
    """
    return {
        str(sid): grp.reset_index(drop=True)
        for sid, grp in events.groupby("session_id_hash", sort=False)
    }


def iter_sessions(events: pd.DataFrame) -> Iterator[tuple[str, pd.DataFrame]]:
    """Yield (session_id, session_events) pairs from a flat events DataFrame."""
    for sid, grp in events.groupby("session_id_hash", sort=False):
        yield str(sid), grp.reset_index(drop=True)


# ---------------------------------------------------------- utility functions --

def get_session_events(
    index: dict[str, pd.DataFrame],
    session_id: str,
) -> pd.DataFrame:
    """Return the events for a given session, or an empty DataFrame."""
    return index.get(session_id, pd.DataFrame(columns=BROWSING_COLS))


def get_observed_products(events: pd.DataFrame) -> list[str]:
    """Return the ordered list of unique product SKUs seen in a session."""
    return (
        events.loc[events["product_sku_hash"] != "", "product_sku_hash"]
        .unique()
        .tolist()
    )


def filter_product_events(
    events: pd.DataFrame,
    actions: set[str] | frozenset[str] | None = None,
) -> pd.DataFrame:
    """Return only rows that have a non-empty product SKU.

    Parameters
    ----------
    events:
        Session events DataFrame.
    actions:
        If provided, further restrict to rows whose product_action is in
        this set.  E.g. ``{"detail", "add"}``.

    Returns
    -------
    pd.DataFrame with reset index.
    """
    mask = events["product_sku_hash"] != ""
    if actions is not None:
        mask = mask & events["product_action"].isin(actions)
    return events.loc[mask].reset_index(drop=True)


def has_detail(events: pd.DataFrame) -> bool:
    """True if the session contains at least one product detail view."""
    return "detail" in events["product_action"].values


def has_add(events: pd.DataFrame) -> bool:
    """True if the session contains at least one add-to-cart event."""
    return "add" in events["product_action"].values


def has_purchase(events: pd.DataFrame) -> bool:
    """True if the session contains at least one purchase event."""
    return "purchase" in events["product_action"].values


def session_length(events: pd.DataFrame) -> int:
    """Total number of events in a session."""
    return len(events)


def session_duration_ms(events: pd.DataFrame) -> int | None:
    """Wall-clock duration of the session in milliseconds.

    Returns None if fewer than two valid timestamps are available.
    """
    valid_ts = events["server_timestamp_epoch_ms"].dropna()
    if len(valid_ts) < 2:
        return None
    return int(valid_ts.max() - valid_ts.min())


def last_event(events: pd.DataFrame) -> pd.Series | None:
    """Return the last row of the session, or None if empty."""
    if events.empty:
        return None
    return events.iloc[-1]


def truncate_session(
    events: pd.DataFrame,
    *,
    observed_frac: float = 0.5,
    min_observed: int = 1,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a session into an observed prefix and a future suffix.

    Parameters
    ----------
    events:
        Session events, sorted chronologically.
    observed_frac:
        Fraction of events to treat as observed context (default: first half).
    min_observed:
        Minimum number of observed events; prevents empty prefixes.

    Returns
    -------
    (observed, future) DataFrames with reset indices.
    """
    n = len(events)
    split = max(min_observed, int(n * observed_frac))
    split = min(split, n)
    return events.iloc[:split].reset_index(drop=True), events.iloc[split:].reset_index(drop=True)


# ------------------------------------------------------------------- summary --

def summarize_sessions(events: pd.DataFrame) -> dict:
    """Return a quick statistics dictionary for a set of browsing events.

    Useful for sanity-checks after loading a sample.
    """
    n_rows = len(events)
    n_sessions = events["session_id_hash"].nunique()
    has_sku = events["product_sku_hash"] != ""
    n_products = events.loc[has_sku, "product_sku_hash"].nunique()

    action_counts: dict[str, int] = (
        events.loc[has_sku, "product_action"].value_counts().to_dict()
    )

    # Per-session action flags
    session_actions = (
        events[has_sku]
        .groupby("session_id_hash")["product_action"]
        .apply(frozenset)
    )
    sessions_with = {
        action: int((session_actions.apply(lambda s, a=action: a in s)).sum())
        for action in ["detail", "add", "purchase", "remove"]
    }

    return {
        "total_rows": n_rows,
        "unique_sessions": n_sessions,
        "unique_products": n_products,
        "product_action_counts": action_counts,
        "sessions_with": sessions_with,
    }


# --------------------------------------------------------------- persistence --

def save_session_sample(
    events: pd.DataFrame,
    output_path: Path | None = None,
    *,
    n_sessions: int = 10_000,
    seed: int = 42,
) -> Path:
    """Save a deterministic sample of sessions to parquet.

    Parameters
    ----------
    events:
        Full or partially-loaded events DataFrame.
    output_path:
        Destination file path.  Defaults to
        ``v2/data/coveo/processed/session_sample.parquet``.
    n_sessions:
        Number of sessions to include in the sample.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    Path to the written file.
    """
    if output_path is None:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        output_path = PROCESSED_DIR / "session_sample.parquet"

    unique = events.loc[events["session_id_hash"] != "", "session_id_hash"].unique()
    if len(unique) > n_sessions:
        rng = np.random.RandomState(seed)
        chosen = rng.choice(unique, size=n_sessions, replace=False)
        sample = events[events["session_id_hash"].isin(chosen)].copy()
    else:
        sample = events.copy()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sample.to_parquet(output_path, index=False)
    return output_path


# --------------------------------------------------------------------- CLI ---

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load, inspect, and optionally persist a session sample."
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=500_000,
        help="Number of raw CSV rows to load (default: 500 000).",
    )
    parser.add_argument(
        "--sample-sessions",
        type=int,
        default=None,
        help="If set, further restrict to N random sessions after row loading.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Write session sample to data/coveo/processed/session_sample.parquet.",
    )
    parser.add_argument(
        "--n-sessions-save",
        type=int,
        default=10_000,
        help="Number of sessions in the saved sample (default: 10 000).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )
    args = parser.parse_args()

    print(f"Loading up to {args.max_rows:,} rows from:\n  {BROWSING_RAW}")

    events = load_browsing_events(
        max_rows=args.max_rows,
        sample_sessions=args.sample_sessions,
        seed=args.seed,
    )

    print(f"Loaded {len(events):,} rows.")

    summary = summarize_sessions(events)
    printable = {
        "total_rows": summary["total_rows"],
        "unique_sessions": summary["unique_sessions"],
        "unique_products": summary["unique_products"],
        "product_action_counts": summary["product_action_counts"],
        "sessions_with": summary["sessions_with"],
    }
    print(json.dumps(printable, indent=2))

    # Show a single sample session
    index = build_session_index(events)
    sample_sid = next(iter(index))
    sample_events = index[sample_sid]
    print(f"\nSample session [{sample_sid}]  ({session_length(sample_events)} events)")
    print(f"  has_detail={has_detail(sample_events)}, "
          f"has_add={has_add(sample_events)}, "
          f"has_purchase={has_purchase(sample_events)}")
    print(f"  products: {get_observed_products(sample_events)}")
    print(f"  duration_ms: {session_duration_ms(sample_events)}")
    print()
    print(sample_events[["server_timestamp_epoch_ms", "event_type", "product_action", "product_sku_hash"]].to_string(index=False))

    if args.save:
        path = save_session_sample(
            events,
            n_sessions=args.n_sessions_save,
            seed=args.seed,
        )
        print(f"\nSaved session sample ({args.n_sessions_save:,} sessions) -> {path}")


if __name__ == "__main__":
    main()
