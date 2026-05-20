"""Lightweight semantic features from `overview` and `tagline`.

We use TF-IDF + TruncatedSVD (Latent Semantic Analysis) — sklearn-only,
no torch / transformers dependency. The training-set vectorizer + SVD
are persisted to be re-applied at inference time.

The output is a fixed-width numeric matrix (default n_components=50) that
can be concatenated to the credits-enriched tabular features.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline


@dataclass
class OverviewBundle:
    pipeline: Pipeline  # TF-IDF + LSA
    feature_names: list[str]
    n_components: int


_CLEAN_RE = re.compile(r"[^a-zA-Z0-9 ]+")
_MULTI_WS = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).lower()
    text = _CLEAN_RE.sub(" ", text)
    text = _MULTI_WS.sub(" ", text).strip()
    return text


def combine_texts(overview: Any, tagline: Any) -> str:
    return (normalize_text(overview) + " " + normalize_text(tagline)).strip()


def build_text_series(df: pd.DataFrame) -> pd.Series:
    overview = df["overview"] if "overview" in df.columns else pd.Series([""] * len(df))
    tagline = df["tagline"] if "tagline" in df.columns else pd.Series([""] * len(df))
    return pd.Series(
        [combine_texts(o, t) for o, t in zip(overview, tagline)],
        index=df.index,
    )


def fit_overview_features(
    text_series_train: pd.Series,
    n_components: int = 50,
    max_features: int = 2000,
    min_df: int = 3,
    max_df: float = 0.95,
    random_state: int = 42,
) -> OverviewBundle:
    """Fit TF-IDF + TruncatedSVD on training texts only (no leakage)."""

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    max_features=max_features,
                    min_df=min_df,
                    max_df=max_df,
                    ngram_range=(1, 2),
                    stop_words="english",
                    sublinear_tf=True,
                ),
            ),
            ("svd", TruncatedSVD(n_components=n_components, random_state=random_state)),
        ]
    )
    pipeline.fit(text_series_train.astype(str).tolist())
    feature_names = [f"ov_svd_{i:02d}" for i in range(n_components)]
    return OverviewBundle(pipeline=pipeline, feature_names=feature_names, n_components=n_components)


def transform_overview(bundle: OverviewBundle, text_series: pd.Series) -> pd.DataFrame:
    arr = bundle.pipeline.transform(text_series.astype(str).tolist())
    return pd.DataFrame(arr, columns=bundle.feature_names, index=text_series.index)


def attach_overview_features(
    df: pd.DataFrame, bundle: OverviewBundle, drop_text: bool = False
) -> pd.DataFrame:
    """Append overview LSA features as ov_svd_00 … ov_svd_NN columns."""

    text = build_text_series(df)
    embed = transform_overview(bundle, text).reset_index(drop=True)
    out = df.reset_index(drop=True).copy()
    out = pd.concat([out, embed], axis=1)
    if drop_text:
        for col in ("overview", "tagline"):
            if col in out.columns:
                out = out.drop(columns=col)
    return out
