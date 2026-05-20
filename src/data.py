"""Dataset loading: TMDB pre-release features + credits (notebook 05 contract).

``load_dataset_split`` returns ``(X_train, X_test, y_train, y_test)`` with the
same leakage-safe credits-enriched columns and ``train_test_split`` discipline
as notebooks 05/06 (``test_size=0.2``, ``random_state=42``, ``stratify=y``).

Train-only features (director/actor frequencies, ``production_scale`` tertiles,
``talent_score`` scaler) are fit on **training rows only** and applied to test.
"""

from __future__ import annotations

import ast
import json
import re
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from config import (
    FORBIDDEN_IN_X,
    PROCESSED_MOVIES_CSV,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    TMDB_CREDITS_CSV,
)

# Populated on each ``load_dataset_split`` call (test rows: ``id``, ``title``).
LAST_TEST_META: pd.DataFrame | None = None

BASELINE_CANDIDATES = [
    "budget",
    "runtime",
    "main_genre",
    "original_language",
    "release_month",
    "release_quarter",
    "genre_count",
    "production_company_count",
    "production_country_count",
    "spoken_language_count",
]
STATIC_ENGINEERED = [
    "budget_log",
    "runtime_bucket",
    "international_production",
    "multilingual_movie",
    "release_season",
    "genre_complexity",
    "decade",
]
ENGINEERED_FOR_MODEL = STATIC_ENGINEERED + ["production_scale"]
CREDITS_NUMERIC = [
    "director_movie_count",
    "top_director_flag",
    "top_billed_cast_count",
    "known_actor_count",
    "cast_size",
    "crew_size",
    "writer_count",
    "possible_franchise_flag",
    "ensemble_cast_flag",
    "talent_score",
]
CREDITS_CATEGORICAL = ["director_bucket"]

TOP_DIRECTORS_K = 40
TOP_ACTORS_K = 120
DIRECTOR_BUCKET_TOP_N = 25

_FORBIDDEN_SET = set(FORBIDDEN_IN_X)


def safe_json_list(val: Any) -> list:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return []
        try:
            return json.loads(s)
        except Exception:
            try:
                return ast.literal_eval(s)
            except Exception:
                return []
    return []


def extract_director_name(crew_raw: Any) -> str:
    for job in ("Director", "Co-Director"):
        for c in safe_json_list(crew_raw):
            if not isinstance(c, dict):
                continue
            if str(c.get("job", "")) == job:
                n = c.get("name")
                if n:
                    return str(n).strip()
    return "__missing__"


def _order_key(x: dict) -> int:
    o = x.get("order", 999)
    try:
        return int(o)
    except (TypeError, ValueError):
        return 999


def extract_cast_ordered(cast_raw: Any) -> list[dict]:
    lst = [x for x in safe_json_list(cast_raw) if isinstance(x, dict)]
    lst.sort(key=_order_key)
    return lst


def writer_count_from_crew(crew_raw: Any) -> int:
    n = 0
    for c in safe_json_list(crew_raw):
        if not isinstance(c, dict):
            continue
        dep = str(c.get("department", ""))
        job = str(c.get("job", "")).lower()
        if dep == "Writing" or "writer" in job:
            n += 1
    return n


_FRANCHISE_PAT = re.compile(
    r"\b(part|chapter|returns|begins|rise|sequel|prequel|reloaded|revolutions|legacy)\b|"
    r"\b(ii|iii|iv|v|vi|vii|viii|ix)\b|"
    r"\bvs\.?\b|"
    r"\s2$|\s3$|:?\s2\b|:?\s3\b|\b2:\s|\b3:\s",
    re.I,
)


def franchise_heuristic(title: Any, keywords_raw: Any) -> int:
    parts = []
    if title is not None and not (isinstance(title, float) and pd.isna(title)):
        parts.append(str(title))
    for kw in safe_json_list(keywords_raw):
        if isinstance(kw, dict) and kw.get("name"):
            parts.append(str(kw["name"]))
    blob = " ".join(parts).lower()
    return int(bool(_FRANCHISE_PAT.search(blob)))


def _production_scale_quantiles(train_counts: pd.Series) -> tuple[float, float]:
    t = pd.to_numeric(train_counts, errors="coerce").dropna()
    if t.empty:
        q1, q2 = 0.0, 1.0
    else:
        q1, q2 = float(t.quantile(1 / 3)), float(t.quantile(2 / 3))
    if q1 == q2:
        q2 = q2 + 1e-6
    return q1, q2


def production_scale_from_quantiles(
    apply_counts: pd.Series, q1: float, q2: float
) -> pd.Series:
    def bucket(x: Any) -> str:
        if pd.isna(x):
            return "__missing__"
        xv = float(x)
        if xv <= q1:
            return "indie"
        if xv <= q2:
            return "mid_scale"
        return "large_scale"

    return apply_counts.map(bucket)


def production_scale_from_train(train_counts: pd.Series, apply_counts: pd.Series) -> pd.Series:
    q1, q2 = _production_scale_quantiles(train_counts)
    return production_scale_from_quantiles(apply_counts, q1, q2)


def _budget_log_quantiles(train_budget: pd.Series) -> tuple[float, float]:
    bl = np.log1p(pd.to_numeric(train_budget, errors="coerce").fillna(0).clip(lower=0))
    if bl.empty:
        return 0.0, 1.0
    q1, q2 = float(bl.quantile(1 / 3)), float(bl.quantile(2 / 3))
    if q1 == q2:
        q2 = q2 + 1e-6
    return q1, q2


def budget_bucket_from_quantiles(budget: Any, q1: float, q2: float) -> str:
    if pd.isna(budget):
        return "__missing__"
    x = float(np.log1p(max(float(budget), 0)))
    if x <= q1:
        return "budget_low"
    if x <= q2:
        return "budget_mid"
    return "budget_high"


def _compute_actor_counts(df_train: pd.DataFrame) -> dict[str, int]:
    actor_counts: dict[str, int] = {}
    for _, row in df_train.iterrows():
        cl = extract_cast_ordered(row.get("cast"))
        seen: set[str] = set()
        for ent in cl[:12]:
            nm = ent.get("name")
            if not nm:
                continue
            nm = str(nm).strip()
            if nm in seen:
                continue
            seen.add(nm)
            actor_counts[nm] = actor_counts.get(nm, 0) + 1
    return actor_counts


def _assert_no_leakage(feature_cols: list[str]) -> None:
    leak = set(feature_cols) & _FORBIDDEN_SET
    if leak:
        raise AssertionError(f"Forbidden columns present in feature list: {sorted(leak)}")
    if TARGET_COLUMN in feature_cols:
        raise AssertionError("Target column must not appear in X.")


def baseline_feature_columns_for_frame(df: pd.DataFrame) -> list[str]:
    present_base = [c for c in BASELINE_CANDIDATES if c in df.columns]
    return [c for c in present_base if c not in _FORBIDDEN_SET]


def engineered_feature_columns_for_frame(df: pd.DataFrame) -> list[str]:
    base = baseline_feature_columns_for_frame(df)
    return base + [c for c in ENGINEERED_FOR_MODEL if c in df.columns]


def fit_train_artifacts(df_train: pd.DataFrame) -> dict[str, Any]:
    """Fit train-only mappings used for production scale and talent features."""

    tr_co = df_train["production_company_count"]
    ps_q1, ps_q2 = _production_scale_quantiles(tr_co)
    budget_q1, budget_q2 = _budget_log_quantiles(df_train["budget"])

    dir_counts = df_train.loc[
        df_train["director_name"] != "__missing__", "director_name"
    ].value_counts()
    director_movie_count_map = {str(k): int(v) for k, v in dir_counts.to_dict().items()}
    top_directors = [str(x) for x in dir_counts.nlargest(TOP_DIRECTORS_K).index]
    director_bucket_top_names = [str(x) for x in dir_counts.nlargest(DIRECTOR_BUCKET_TOP_N).index]

    actor_counts = _compute_actor_counts(df_train)
    top_actors = [
        str(k)
        for k in sorted(actor_counts, key=lambda name: actor_counts[name], reverse=True)[
            :TOP_ACTORS_K
        ]
    ]

    tr = df_train.copy()
    tr["_ka"] = 0
    tr["_dm"] = tr["director_name"].map(
        lambda n: 0 if n == "__missing__" else int(director_movie_count_map.get(str(n), 0))
    )
    if "cast" in tr.columns:
        top_actor_set = set(top_actors)

        def _ka(cast_raw: Any) -> int:
            k = 0
            cl = extract_cast_ordered(cast_raw)
            seen: set[str] = set()
            for ent in cl[:12]:
                nm = ent.get("name")
                if not nm:
                    continue
                nm = str(nm).strip()
                if nm in seen:
                    continue
                seen.add(nm)
                if nm in top_actor_set:
                    k += 1
            return k

        tr["_ka"] = tr["cast"].map(_ka)

    talent_scaler = MinMaxScaler()
    talent_scaler.fit(tr[["_ka", "_dm"]].astype(float))

    input_defaults: dict[str, Any] = {}
    for col in BASELINE_CANDIDATES + CREDITS_NUMERIC:
        if col not in df_train.columns:
            continue
        if pd.api.types.is_numeric_dtype(df_train[col]):
            input_defaults[col] = float(df_train[col].median())
    for col in [
        "main_genre",
        "original_language",
        "release_month",
        "release_quarter",
        "runtime_bucket",
        "release_season",
        "genre_complexity",
        "decade",
        "director_name",
        "director_bucket",
    ]:
        if col in df_train.columns:
            mode = df_train[col].dropna().mode()
            input_defaults[col] = str(mode.iloc[0]) if len(mode) else "__missing__"
    input_defaults.setdefault("director_name", "__missing__")

    partial: dict[str, Any] = {
        "production_scale_q1": ps_q1,
        "production_scale_q2": ps_q2,
        "budget_bucket_q1": budget_q1,
        "budget_bucket_q2": budget_q2,
        "director_movie_count_map": director_movie_count_map,
        "top_directors": top_directors,
        "director_bucket_top_names": director_bucket_top_names,
        "actor_counts": actor_counts,
        "top_actors": top_actors,
        "talent_scaler": talent_scaler,
    }
    df_ref = apply_train_artifacts(df_train.copy(), partial)
    baseline_features = baseline_feature_columns_for_frame(df_ref)
    engineered_features = engineered_feature_columns_for_frame(df_ref)
    credits_features = credits_feature_columns_for_frame(df_ref)

    X_ref = finalize_credits_X(df_ref[credits_features])
    num_cols, cat_cols = column_groups_for_credits_pipeline(X_ref)

    return {
        **partial,
        "baseline_features": baseline_features,
        "engineered_features": engineered_features,
        "credits_features": credits_features,
        "numeric_columns": num_cols,
        "categorical_columns": cat_cols,
        "input_defaults": input_defaults,
    }


def apply_train_artifacts(df: pd.DataFrame, artifacts: dict[str, Any]) -> pd.DataFrame:
    """Apply fitted train-only talent / production-scale fields to any frame."""

    out = df.copy()
    ps_q1 = artifacts["production_scale_q1"]
    ps_q2 = artifacts["production_scale_q2"]
    top_directors = set(artifacts["top_directors"])
    top_dir_names = set(artifacts["director_bucket_top_names"])
    top_actors = set(artifacts["top_actors"])
    dir_movie_count_map = artifacts["director_movie_count_map"]
    talent_scaler: MinMaxScaler = artifacts["talent_scaler"]

    if "production_company_count" in out.columns:
        out["production_scale"] = production_scale_from_quantiles(
            out["production_company_count"], ps_q1, ps_q2
        ).astype(str)
    elif "production_scale" not in out.columns:
        out["production_scale"] = "__missing__"

    if "director_name" not in out.columns:
        out["director_name"] = "__missing__"
    out["director_name"] = out["director_name"].fillna("__missing__").astype(str)

    def map_dir_count(name: str) -> int:
        return 0 if name == "__missing__" else int(dir_movie_count_map.get(str(name), 0))

    def map_top_flag(name: str) -> int:
        return int(name in top_directors and name != "__missing__")

    def map_bucket(name: str) -> str:
        if name == "__missing__":
            return "__missing__"
        if name in top_dir_names:
            return name
        return "__other__"

    out["director_movie_count"] = out["director_name"].map(map_dir_count)
    out["top_director_flag"] = out["director_name"].map(map_top_flag)
    out["director_bucket"] = out["director_name"].map(map_bucket)

    if "cast" in out.columns:
        def map_known_actor(cast_raw: Any) -> int:
            k = 0
            cl = extract_cast_ordered(cast_raw)
            seen: set[str] = set()
            for ent in cl[:12]:
                nm = ent.get("name")
                if not nm:
                    continue
                nm = str(nm).strip()
                if nm in seen:
                    continue
                seen.add(nm)
                if nm in top_actors:
                    k += 1
            return k

        out["known_actor_count"] = out["cast"].map(map_known_actor)
    elif "known_actor_count" not in out.columns:
        out["known_actor_count"] = 0

    scaled = talent_scaler.transform(
        out.assign(_ka=out["known_actor_count"], _dm=out["director_movie_count"])[
            ["_ka", "_dm"]
        ].astype(float)
    )
    top_flag = out["top_director_flag"].astype(float).values
    out["talent_score"] = 0.45 * scaled[:, 0] + 0.35 * scaled[:, 1] + 0.20 * top_flag
    return out


def apply_train_only_talent_features(
    df_all: pd.DataFrame, idx_train: np.ndarray, idx_test: np.ndarray
) -> pd.DataFrame:
    artifacts = fit_train_artifacts(df_all.iloc[idx_train])
    return apply_train_artifacts(df_all, artifacts)


def _merge_movies_credits(movies: pd.DataFrame, credits: pd.DataFrame) -> pd.DataFrame:
    try:
        merged = movies.merge(
            credits,
            left_on="id",
            right_on="movie_id",
            how="left",
            suffixes=("", "_cred"),
            validate="one_to_one",
        )
    except Exception:
        merged = movies.merge(
            credits,
            left_on="id",
            right_on="movie_id",
            how="left",
            suffixes=("", "_cred"),
        )
    if "movie_id" in merged.columns:
        merged = merged.drop(columns=["movie_id"])
    for c in list(merged.columns):
        if c in ("title_cred", "title_credits"):
            merged = merged.drop(columns=[c])
    return merged


def _add_static_credits_and_tabular(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    directors, cast_sizes, crew_sizes, writers, top_billed, franch, ensemble = [], [], [], [], [], [], []
    for _, row in d.iterrows():
        cr, ca = row.get("crew"), row.get("cast")
        directors.append(extract_director_name(cr))
        cl = extract_cast_ordered(ca)
        cast_sizes.append(len(cl))
        crew_sizes.append(len(safe_json_list(cr)))
        writers.append(writer_count_from_crew(cr))
        billed = sum(1 for ent in cl[:5] if ent.get("name"))
        top_billed.append(billed)
        franch.append(franchise_heuristic(row.get("title"), row.get("keywords")))
        ensemble.append(int(len(cl) >= 12))
    d["director_name"] = directors
    d["cast_size"] = cast_sizes
    d["crew_size"] = crew_sizes
    d["writer_count"] = writers
    d["top_billed_cast_count"] = top_billed
    d["possible_franchise_flag"] = franch
    d["ensemble_cast_flag"] = ensemble

    d["budget_log"] = np.log1p(d["budget"].clip(lower=0))

    def _runtime_bucket(v: Any) -> str:
        if pd.isna(v):
            return "__missing__"
        r = float(v)
        if r < 90:
            return "short"
        if r <= 120:
            return "medium"
        return "long"

    d["runtime_bucket"] = d["runtime"].map(_runtime_bucket)
    d["international_production"] = (d["production_country_count"].fillna(0) > 1).astype(int)
    d["multilingual_movie"] = (d["spoken_language_count"].fillna(0) > 1).astype(int)

    def _season(m: Any) -> str:
        if pd.isna(m):
            return "__missing__"
        mi = int(m)
        if mi in (12, 1, 2):
            return "winter"
        if mi in (3, 4, 5):
            return "spring"
        if mi in (6, 7, 8):
            return "summer"
        if mi in (9, 10, 11):
            return "fall"
        return "__missing__"

    if "release_month" in d.columns:
        d["release_season"] = d["release_month"].map(_season)
    else:
        d["release_season"] = "__missing__"

    def _gc(gc: Any) -> str:
        if pd.isna(gc):
            return "__missing__"
        g = int(gc)
        if g <= 1:
            return "focused"
        if g <= 3:
            return "mixed"
        return "hybrid"

    d["genre_complexity"] = d["genre_count"].map(_gc)
    if "release_year" in d.columns:
        yr = pd.to_numeric(d["release_year"], errors="coerce")

        def _dec(y: Any) -> str:
            if pd.isna(y):
                return "__missing__"
            yi = int(y)
            return f"{(yi // 10) * 10}s"

        d["decade"] = yr.map(_dec)
    else:
        d["decade"] = "__missing__"
    d["production_scale"] = "__pending__"
    return d


def build_modeling_frame() -> pd.DataFrame:
    """Merged movies + credits with static (row-local) engineered columns.

    Does **not** include train-only talent frequency fields or final ``production_scale``.
    Use ``load_dataset_split()`` for ML-ready matrices.
    """

    if not PROCESSED_MOVIES_CSV.exists():
        raise FileNotFoundError(f"Missing processed movies: {PROCESSED_MOVIES_CSV}")
    movies = pd.read_csv(PROCESSED_MOVIES_CSV)
    if not TMDB_CREDITS_CSV.exists():
        raise FileNotFoundError(f"Missing credits: {TMDB_CREDITS_CSV}")
    credits = pd.read_csv(TMDB_CREDITS_CSV)
    merged = _merge_movies_credits(movies, credits)
    return _add_static_credits_and_tabular(merged)


def load_full_modeling_data() -> pd.DataFrame:
    """Alias for :func:`build_modeling_frame` (Streamlit / inspection)."""

    return build_modeling_frame()


def credits_feature_columns_for_frame(df: pd.DataFrame) -> list[str]:
    return engineered_feature_columns_for_frame(df) + [
        c for c in CREDITS_NUMERIC + CREDITS_CATEGORICAL if c in df.columns
    ]


def finalize_credits_X(X: pd.DataFrame) -> pd.DataFrame:
    """Match notebook preprocessing for stable OHE (string categoricals)."""

    X = X.copy()
    baseline_cat = ["main_genre", "original_language", "release_month", "release_quarter"]
    extra_cat = ["runtime_bucket", "production_scale", "release_season", "genre_complexity", "decade"]
    credits_cat = list(CREDITS_CATEGORICAL)
    cat_cols = [c for c in baseline_cat + extra_cat + credits_cat if c in X.columns]

    for col in ["main_genre", "original_language"]:
        if col in X.columns:
            X[col] = X[col].astype("string").fillna("__missing__")
    for col in ["release_month", "release_quarter"]:
        if col in X.columns:
            X[col] = X[col].apply(lambda v: "__missing__" if pd.isna(v) else str(int(v)))
    for col in cat_cols:
        X[col] = X[col].astype(str)
    return X


def column_groups_for_credits_pipeline(X: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Numeric vs categorical column lists (order preserved from ``X.columns``)."""

    baseline_cat = ["main_genre", "original_language", "release_month", "release_quarter"]
    extra_cat = ["runtime_bucket", "production_scale", "release_season", "genre_complexity", "decade"]
    credits_cat = list(CREDITS_CATEGORICAL)
    cat_set = set(baseline_cat + extra_cat + credits_cat)
    cat_cols = [c for c in X.columns if c in cat_set]
    num_cols = [c for c in X.columns if c not in cat_set]
    return num_cols, cat_cols


def _regime_split_dict(
    df_model: pd.DataFrame,
    feature_cols: list[str],
    idx_train: np.ndarray,
    idx_test: np.ndarray,
) -> dict[str, Any]:
    _assert_no_leakage(feature_cols)
    missing = [c for c in feature_cols if c not in df_model.columns]
    if missing:
        raise ValueError(f"Expected feature columns missing from frame: {missing}")

    X = finalize_credits_X(df_model[feature_cols])
    num_cols, cat_cols = column_groups_for_credits_pipeline(X)
    return {
        "X_train": X.iloc[idx_train],
        "X_test": X.iloc[idx_test],
        "feature_columns": feature_cols,
        "num_cols": num_cols,
        "cat_cols": cat_cols,
    }


def load_feature_regime_splits() -> dict[str, Any]:
    """Shared stratified split with baseline, engineered, and credits feature regimes."""

    df = build_modeling_frame()
    y_all = df[TARGET_COLUMN].astype(str)
    idx = np.arange(len(df))
    idx_train, idx_test = train_test_split(
        idx, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_all
    )

    artifacts = fit_train_artifacts(df.iloc[idx_train])
    df_model = apply_train_artifacts(df, artifacts)

    baseline_cols = baseline_feature_columns_for_frame(df_model)
    engineered_cols = engineered_feature_columns_for_frame(df_model)
    credits_cols = credits_feature_columns_for_frame(df_model)

    meta_cols = [
        c
        for c in (
            "id",
            "title",
            "original_title",
            "budget",
            "runtime",
            "main_genre",
            "director_name",
            "cast_size",
            "crew_size",
            "known_actor_count",
            "possible_franchise_flag",
            "runtime_bucket",
            "production_scale",
            "talent_score",
        )
        if c in df_model.columns
    ]
    train_meta = df_model.iloc[idx_train][meta_cols].copy().reset_index(drop=True)
    test_meta = df_model.iloc[idx_test][meta_cols].copy().reset_index(drop=True)

    return {
        "baseline": _regime_split_dict(df_model, baseline_cols, idx_train, idx_test),
        "engineered": _regime_split_dict(df_model, engineered_cols, idx_train, idx_test),
        "credits": _regime_split_dict(df_model, credits_cols, idx_train, idx_test),
        "y_train": y_all.iloc[idx_train],
        "y_test": y_all.iloc[idx_test],
        "train_meta": train_meta,
        "test_meta": test_meta,
        "df_model": df_model,
        "idx_train": idx_train,
        "idx_test": idx_test,
        "artifacts": artifacts,
    }


def load_dataset_split() -> tuple[Any, Any, Any, Any]:
    """Load merged data, apply notebook-05 feature contract, stratified split, return X/y."""

    global LAST_TEST_META

    splits = load_feature_regime_splits()
    credits = splits["credits"]
    y_train, y_test = splits["y_train"], splits["y_test"]
    X_train, X_test = credits["X_train"], credits["X_test"]
    feature_cols = credits["feature_columns"]

    meta = splits["test_meta"]
    meta_cols = [c for c in ("id", "title", "original_title") if c in meta.columns]
    if meta_cols:
        LAST_TEST_META = meta[meta_cols].copy()
    else:
        LAST_TEST_META = None

    print("===== load_dataset_split =====")
    print("n_features:", len(feature_cols))
    print("X_train shape:", X_train.shape, "| X_test shape:", X_test.shape)
    print("Train class %:")
    print((y_train.value_counts(normalize=True) * 100).round(1).to_string())
    print("Test class %:")
    print((y_test.value_counts(normalize=True) * 100).round(1).to_string())

    return X_train, X_test, y_train, y_test
