"""Historical comparables: nearest neighbours from the cleaned movies dataset.

Given a user-defined movie profile we return the 3 closest real movies from the
TMDB processed corpus. Distance is computed on a small set of standardized
numerical and one-hot categorical features that mirror the user inputs.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

import config
import data

NUMERIC_KEYS = [
    "budget",
    "runtime",
    "cast_size",
    "crew_size",
    "writer_count",
    "production_company_count",
    "production_country_count",
    "spoken_language_count",
    "genre_count",
    "known_actor_count",
    "top_billed_cast_count",
]

CATEGORICAL_KEYS = ["main_genre", "original_language", "release_season"]

FLAG_KEYS = ["possible_franchise_flag", "ensemble_cast_flag", "top_director_flag"]


def _build_enriched_corpus() -> pd.DataFrame:
    """Return the merged movies+credits dataset with all engineered fields."""

    splits = data.load_feature_regime_splits()
    df = splits["df_model"].copy()
    keep_cols = [
        "id",
        "title",
        "release_year",
        "release_month",
        "release_season",
        "main_genre",
        "original_language",
        "budget",
        "revenue",
        "runtime",
        "cast_size",
        "crew_size",
        "writer_count",
        "production_company_count",
        "production_country_count",
        "spoken_language_count",
        "genre_count",
        "known_actor_count",
        "top_billed_cast_count",
        "possible_franchise_flag",
        "ensemble_cast_flag",
        "top_director_flag",
        "director_name",
        "talent_score",
        "movie_success_class",
        "roi",
    ]
    keep_cols = [c for c in keep_cols if c in df.columns]
    return df[keep_cols].reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_corpus() -> pd.DataFrame:
    try:
        return _build_enriched_corpus()
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_resource(show_spinner=False)
def _fit_corpus_features():
    df = load_corpus()
    if df.empty:
        return None

    num = df[NUMERIC_KEYS].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    means = num.mean(axis=0)
    stds = num.std(axis=0).replace(0, 1)
    num_std = (num - means) / stds

    cat_dummies = pd.get_dummies(df[CATEGORICAL_KEYS].astype(str), prefix=CATEGORICAL_KEYS)
    flags = df[FLAG_KEYS].fillna(0).astype(float)

    matrix = pd.concat([num_std, cat_dummies, flags], axis=1).fillna(0.0)
    return {
        "matrix": matrix.to_numpy(dtype=float),
        "columns": matrix.columns.tolist(),
        "means": means,
        "stds": stds,
        "df": df,
    }


def _user_vector(user_inputs: dict[str, Any], corpus: dict[str, Any]) -> np.ndarray | None:
    means = corpus["means"]
    stds = corpus["stds"]
    columns = corpus["columns"]

    vec = pd.Series(0.0, index=columns)

    for key in NUMERIC_KEYS:
        if key in user_inputs and user_inputs[key] is not None:
            try:
                raw = float(user_inputs[key])
            except (TypeError, ValueError):
                raw = float(means.get(key, 0.0))
        else:
            raw = float(means.get(key, 0.0))
        std = float(stds.get(key, 1.0)) or 1.0
        if key in vec.index:
            vec[key] = (raw - float(means.get(key, 0.0))) / std

    for key in CATEGORICAL_KEYS:
        val = user_inputs.get(key, "__missing__")
        if val is None:
            val = "__missing__"
        col = f"{key}_{val}"
        if col in vec.index:
            vec[col] = 1.0

    for key in FLAG_KEYS:
        if key in vec.index:
            try:
                vec[key] = float(int(user_inputs.get(key, 0) or 0))
            except (TypeError, ValueError):
                vec[key] = 0.0

    return vec.to_numpy(dtype=float)


def find_comparables(user_inputs: dict[str, Any], k: int = 3) -> pd.DataFrame:
    corpus = _fit_corpus_features()
    if corpus is None:
        return pd.DataFrame()

    target = _user_vector(user_inputs, corpus)
    if target is None:
        return pd.DataFrame()

    matrix = corpus["matrix"]

    # cosine similarity (vectors include both numeric & one-hot — both meaningful)
    t_norm = np.linalg.norm(target) or 1.0
    m_norm = np.linalg.norm(matrix, axis=1)
    m_norm[m_norm == 0] = 1.0
    sims = (matrix @ target) / (m_norm * t_norm)

    df = corpus["df"].copy()
    df["similarity"] = sims
    df = df.sort_values("similarity", ascending=False)

    # de-duplicate on title (safety: TMDB may have near-duplicates)
    df = df.drop_duplicates(subset="title", keep="first")
    return df.head(k).reset_index(drop=True)
