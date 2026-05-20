"""Inference helpers for the Streamlit prediction simulator.

The app prefers the production champion (`models/production_champion.joblib`)
when present — it is the tuned Logistic Regression refit on a *cleaned* 25-feature
set by ``scripts/refit_clean_champion.py`` (the original 29-feature tuned LR was
marginally higher in macro-F1 but had multicollinearity issues — see the script
for details). Otherwise the loader falls back to the legacy credits LR
(`models/credits_logistic_regression.joblib`) for backwards compatibility with
``scripts/train_models.py``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

import config
import data
import model_io


_PRODUCTION_MODEL_FILE = config.MODELS_DIR / "production_champion.joblib"
_PRODUCTION_ARTIFACTS_FILE = config.MODELS_DIR / "production_champion_artifacts.joblib"


def _load_production_bundle() -> tuple[Any, Any, dict[str, Any]] | None:
    """Return (pipeline, artifacts, meta) if production champion is on disk."""
    if not _PRODUCTION_MODEL_FILE.exists() or not _PRODUCTION_ARTIFACTS_FILE.exists():
        return None
    saved = model_io.load_model(_PRODUCTION_MODEL_FILE)
    artifacts = model_io.load_model(_PRODUCTION_ARTIFACTS_FILE)
    pipeline = saved.get("pipeline") if isinstance(saved, dict) else saved
    meta = {
        "label": saved.get("label", "production_champion") if isinstance(saved, dict) else "production_champion",
        "use_full_features": bool(saved.get("use_full_features", False)) if isinstance(saved, dict) else False,
        "feature_columns": saved.get("feature_columns") if isinstance(saved, dict) else None,
    }
    return pipeline, artifacts, meta


def load_champion_bundle() -> dict[str, Any]:
    """Load production champion if available, else fall back to legacy LR."""
    prod = _load_production_bundle()
    if prod is not None:
        pipeline, artifacts, meta = prod
        return {"model": pipeline, "artifacts": artifacts, "meta": meta}

    legacy_model = model_io.load_model(config.MODELS["credits_logistic_regression"]["path"])
    legacy_artifacts = model_io.load_model(config.TRAIN_ARTIFACTS_FILE)
    return {
        "model": legacy_model,
        "artifacts": legacy_artifacts,
        "meta": {"label": "legacy_logreg_credits", "use_full_features": False, "feature_columns": None},
    }


def _fill_defaults(user_inputs: dict[str, Any], artifacts: dict[str, Any]) -> dict[str, Any]:
    defaults = dict(artifacts.get("input_defaults", {}))
    defaults.update({k: v for k, v in user_inputs.items() if v is not None})
    return defaults


def _apply_static_engineering(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    budget = float(out.get("budget", 0) or 0)
    out["budget_log"] = float(np.log1p(max(budget, 0)))

    runtime = out.get("runtime")
    if runtime is None or (isinstance(runtime, float) and pd.isna(runtime)):
        out["runtime_bucket"] = "__missing__"
    else:
        r = float(runtime)
        if r < 90:
            out["runtime_bucket"] = "short"
        elif r <= 120:
            out["runtime_bucket"] = "medium"
        else:
            out["runtime_bucket"] = "long"

    pcc = float(out.get("production_country_count", 0) or 0)
    slc = float(out.get("spoken_language_count", 0) or 0)
    out["international_production"] = int(pcc > 1)
    out["multilingual_movie"] = int(slc > 1)

    month = out.get("release_month")
    if month is None or (isinstance(month, float) and pd.isna(month)):
        out["release_season"] = "__missing__"
    else:
        mi = int(month)
        if mi in (12, 1, 2):
            out["release_season"] = "winter"
        elif mi in (3, 4, 5):
            out["release_season"] = "spring"
        elif mi in (6, 7, 8):
            out["release_season"] = "summer"
        elif mi in (9, 10, 11):
            out["release_season"] = "fall"
        else:
            out["release_season"] = "__missing__"

    gc = out.get("genre_count")
    if gc is None or (isinstance(gc, float) and pd.isna(gc)):
        out["genre_complexity"] = "__missing__"
    else:
        g = int(gc)
        if g <= 1:
            out["genre_complexity"] = "focused"
        elif g <= 3:
            out["genre_complexity"] = "mixed"
        else:
            out["genre_complexity"] = "hybrid"

    if out.get("release_year") is not None and not (
        isinstance(out["release_year"], float) and pd.isna(out["release_year"])
    ):
        yi = int(out["release_year"])
        out["decade"] = f"{(yi // 10) * 10}s"
    else:
        out["decade"] = out.get("decade", "__missing__")

    for col in ("main_genre", "original_language"):
        if col in out and out[col] is not None:
            out[col] = str(out[col])
        else:
            out[col] = "__missing__"

    for col in ("release_month", "release_quarter"):
        if col in out and out[col] is not None and not (
            isinstance(out[col], float) and pd.isna(out[col])
        ):
            out[col] = str(int(out[col]))
        else:
            out[col] = "__missing__"

    out.setdefault("director_name", "__missing__")
    out["director_name"] = str(out["director_name"])

    for col in (
        "cast_size",
        "crew_size",
        "writer_count",
        "top_billed_cast_count",
        "possible_franchise_flag",
        "ensemble_cast_flag",
    ):
        out.setdefault(col, 0)
        out[col] = int(out[col] or 0)

    return out


def build_input_row(user_inputs: dict[str, Any], artifacts: dict[str, Any]) -> pd.DataFrame:
    """Build one credits-regime feature row from user-friendly inputs."""

    filled = _fill_defaults(user_inputs, artifacts)
    filled = _apply_static_engineering(filled)

    if "top_director_flag" in user_inputs and user_inputs["top_director_flag"] is not None:
        filled["top_director_flag"] = int(user_inputs["top_director_flag"])

    row_df = pd.DataFrame([filled])
    row_df = data.apply_train_artifacts(row_df, artifacts)

    if "known_actor_count" in user_inputs and user_inputs["known_actor_count"] is not None:
        row_df["known_actor_count"] = int(user_inputs["known_actor_count"])
        scaled = artifacts["talent_scaler"].transform(
            row_df.assign(
                _ka=row_df["known_actor_count"], _dm=row_df["director_movie_count"]
            )[["_ka", "_dm"]].astype(float)
        )
        top_flag = row_df["top_director_flag"].astype(float).values
        row_df["talent_score"] = 0.45 * scaled[:, 0] + 0.35 * scaled[:, 1] + 0.20 * top_flag

    if "top_director_flag" in user_inputs and user_inputs["top_director_flag"] is not None:
        row_df["top_director_flag"] = int(user_inputs["top_director_flag"])

    feature_cols = artifacts["credits_features"]
    for col in feature_cols:
        if col not in row_df.columns:
            default = artifacts.get("input_defaults", {}).get(col, 0)
            row_df[col] = default

    return data.finalize_credits_X(row_df[feature_cols])


def _risk_level(confidence: float) -> str:
    if confidence < 0.45:
        return "Low confidence — analyst review required"
    if confidence < 0.65:
        return "Moderate confidence — use as discussion input"
    return "Higher confidence — still validate with market context"


def _business_interpretation(prediction: str, confidence: float, risk: str) -> str:
    label = {"flop": "potential flop", "average": "average commercial candidate", "hit": "possible hit"}.get(
        prediction, prediction
    )
    return (
        f"The model classifies this package as a {label} (confidence {confidence:.0%}). "
        f"{risk}. Use alongside market context — not as an automatic greenlight signal."
    )


def _augment_with_overview(X: pd.DataFrame, artifacts: dict[str, Any]) -> pd.DataFrame:
    """Append overview LSA features when the production champion uses them."""
    bundle = artifacts.get("overview_bundle")
    if bundle is None:
        return X
    n_components = getattr(bundle, "n_components", 50)
    cols = artifacts.get("overview_features", [f"ov_svd_{i:02d}" for i in range(n_components)])
    zeros = pd.DataFrame(
        np.zeros((len(X), len(cols))),
        columns=cols,
        index=X.index,
    )
    return pd.concat([X.reset_index(drop=True), zeros.reset_index(drop=True)], axis=1)


def _model_classes(model) -> list:
    classes = getattr(model, "classes_", None)
    if classes is not None:
        return list(classes)
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        return list(model.named_steps["clf"].classes_)
    return ["flop", "average", "hit"]


def predict_movie_profile(user_inputs: dict[str, Any]) -> dict[str, Any]:
    """Predict success class and return probabilities, confidence, and risk guidance."""

    bundle = load_champion_bundle()
    model = bundle["model"]
    artifacts = bundle["artifacts"]
    meta = bundle.get("meta", {})

    X = build_input_row(user_inputs, artifacts)

    # Production champion may expect extra overview-LSA columns.
    needs_full = meta.get("use_full_features", False)
    if needs_full:
        X = _augment_with_overview(X, artifacts)
        # If feature_columns is known, reorder + add missing
        feats = meta.get("feature_columns")
        if feats:
            for col in feats:
                if col not in X.columns:
                    X[col] = 0
            X = X[feats]

    prediction = str(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    classes = _model_classes(model)
    prob_dict = {str(c): float(proba[i]) for i, c in enumerate(classes)}
    confidence = float(max(proba))
    risk = _risk_level(confidence)

    return {
        "prediction": prediction,
        "probabilities": prob_dict,
        "confidence": confidence,
        "risk_level": risk,
        "business_interpretation": _business_interpretation(prediction, confidence, risk),
        "model_label": meta.get("label", ""),
    }
