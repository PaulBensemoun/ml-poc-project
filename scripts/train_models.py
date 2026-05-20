#!/usr/bin/env python3
"""Train regime models, champion credits LR, and app-ready result artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import config
import data
import metrics
import model_io
from results import write_metrics


def _build_lr_pipeline(num_cols: list[str], cat_cols: list[str]) -> Pipeline:
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    cat_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    transformers = []
    if num_cols:
        transformers.append(("num", num_pipe, num_cols))
    if cat_cols:
        transformers.append(("cat", cat_pipe, cat_cols))
    prep = ColumnTransformer(transformers=transformers)
    clf = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        random_state=config.RANDOM_STATE,
        solver="lbfgs",
    )
    return Pipeline([("prep", prep), ("clf", clf)])


def _train_regime(
    regime_key: str,
    regime: dict,
    y_train: pd.Series,
    y_test: pd.Series,
) -> tuple[Pipeline, dict[str, float], np.ndarray, np.ndarray, list]:
    pipe = _build_lr_pipeline(regime["num_cols"], regime["cat_cols"])
    pipe.fit(regime["X_train"], y_train)
    y_pred = pipe.predict(regime["X_test"])
    m = metrics.compute_metrics(y_test, y_pred)
    proba = pipe.predict_proba(regime["X_test"])
    classes = list(pipe.named_steps["clf"].classes_)
    return pipe, m, y_pred, proba, classes


def _proba_columns(proba: np.ndarray, classes: list, prefix: str) -> pd.DataFrame:
    out = {}
    for j, c in enumerate(classes):
        out[f"{prefix}p_{c}"] = proba[:, j]
    return pd.DataFrame(out)


def _p_true(proba: np.ndarray, classes: list, y_true: np.ndarray) -> np.ndarray:
    class_to_idx = {c: i for i, c in enumerate(classes)}
    idx = [class_to_idx.get(str(y), 0) for y in y_true]
    return proba[np.arange(len(idx)), idx]


def _build_error_analysis_full(
    splits: dict,
    y_test: pd.Series,
    pred_baseline: np.ndarray,
    proba_baseline: np.ndarray,
    classes_b: list,
    pred_credits: np.ndarray,
    proba_credits: np.ndarray,
    classes_c: list,
) -> pd.DataFrame:
    test_meta = splits["test_meta"].copy()
    artifacts = splits["artifacts"]
    df_model = splits["df_model"]
    idx_test = splits["idx_test"]
    te_full = df_model.iloc[idx_test].reset_index(drop=True)

    err = pd.DataFrame({"y_true": y_test.values})
    err["y_pred_baseline"] = pred_baseline
    err["y_pred_credits"] = pred_credits

    err = pd.concat(
        [
            err,
            _proba_columns(proba_baseline, classes_b, "base_"),
            _proba_columns(proba_credits, classes_c, ""),
        ],
        axis=1,
    )
    err["base_confidence"] = proba_baseline.max(axis=1)
    err["confidence"] = proba_credits.max(axis=1)
    err["p_true_baseline"] = _p_true(proba_baseline, classes_b, y_test.values)
    err["p_true_credits"] = _p_true(proba_credits, classes_c, y_test.values)
    err["delta_p_true"] = err["p_true_credits"] - err["p_true_baseline"]

    err["baseline_correct"] = (err["y_true"] == err["y_pred_baseline"]).astype(int)
    err["credits_correct"] = (err["y_true"] == err["y_pred_credits"]).astype(int)

    def transition_row(r: pd.Series) -> str:
        b, c = bool(r["baseline_correct"]), bool(r["credits_correct"])
        if b and c:
            return "stable_correct"
        if (not b) and (not c):
            return "stable_wrong"
        if (not b) and c:
            return "wrong_to_correct"
        return "correct_to_wrong"

    err["transition"] = err.apply(transition_row, axis=1)

    for col in ("id", "title", "original_title"):
        if col in test_meta.columns:
            err[col] = test_meta[col].values

    for col in (
        "main_genre",
        "budget",
        "runtime",
        "production_scale",
        "talent_score",
        "cast_size",
        "crew_size",
        "known_actor_count",
        "possible_franchise_flag",
        "director_name",
        "runtime_bucket",
    ):
        if col in te_full.columns:
            err[col] = te_full[col].values

    bq1, bq2 = artifacts["budget_bucket_q1"], artifacts["budget_bucket_q2"]
    if "budget" in err.columns:
        err["budget_bucket"] = [
            data.budget_bucket_from_quantiles(v, bq1, bq2) for v in err["budget"].values
        ]

    return err


def _build_case_studies(error_full: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    strong = error_full[
        (error_full["credits_correct"] == 1) & (error_full["confidence"] >= 0.65)
    ].sort_values("confidence", ascending=False)
    if len(strong):
        part = strong.head(10).copy()
        part["case_type"] = "strong_correct"
        frames.append(part)

    rescue = error_full[error_full["transition"] == "wrong_to_correct"].sort_values(
        "delta_p_true", ascending=False
    )
    if len(rescue):
        part = rescue.head(10).copy()
        part["case_type"] = "credits_rescue"
        frames.append(part)

    failures = error_full[
        (error_full["credits_correct"] == 0) & (error_full["confidence"] >= 0.65)
    ].sort_values("confidence", ascending=False)
    if len(failures):
        part = failures.head(10).copy()
        part["case_type"] = "high_confidence_failure"
        frames.append(part)

    if not frames:
        return pd.DataFrame(columns=list(error_full.columns) + ["case_type"])

    return pd.concat(frames, ignore_index=True)


def _build_app_kpis(
    n_movies_total: int,
    n_test: int,
    champion_metrics: dict[str, float],
    error_full: pd.DataFrame,
) -> dict:
    vc = error_full["transition"].value_counts()
    return {
        "n_movies_total": n_movies_total,
        "n_test": n_test,
        "champion_model_name": config.MODELS["credits_logistic_regression"]["name"],
        "champion_accuracy": champion_metrics["accuracy"],
        "champion_macro_f1": champion_metrics["macro_f1"],
        "f1_flop": champion_metrics["f1_flop"],
        "f1_average": champion_metrics["f1_average"],
        "f1_hit": champion_metrics["f1_hit"],
        "n_stable_correct": int(vc.get("stable_correct", 0)),
        "n_stable_wrong": int(vc.get("stable_wrong", 0)),
        "n_wrong_to_correct": int(vc.get("wrong_to_correct", 0)),
        "n_correct_to_wrong": int(vc.get("correct_to_wrong", 0)),
    }


def main() -> None:
    splits = data.load_feature_regime_splits()
    y_train, y_test = splits["y_train"], splits["y_test"]
    artifacts = splits["artifacts"]

    regime_rows: list[dict] = []
    pipes: dict[str, Pipeline] = {}

    for regime_key in ("baseline", "engineered", "credits"):
        regime = splits[regime_key]
        pipe, m, y_pred, proba, classes = _train_regime(regime_key, regime, y_train, y_test)
        pipes[regime_key] = pipe
        regime_rows.append(
            {
                "model": "logistic_regression",
                "regime": regime_key,
                **m,
            }
        )
        if regime_key == "credits":
            credits_pred, credits_proba, credits_classes = y_pred, proba, classes
        if regime_key == "baseline":
            baseline_pred, baseline_proba, baseline_classes = y_pred, proba, classes

    champion_path = config.MODELS["credits_logistic_regression"]["path"]
    model_io.save_model(pipes["credits"], champion_path)
    model_io.save_model(artifacts, config.TRAIN_ARTIFACTS_FILE)

    champion_m = regime_rows[-1]
    metrics_df = write_metrics(
        [
            {
                "model_key": "credits_logistic_regression",
                "model_name": config.MODELS["credits_logistic_regression"]["name"],
                "model_path": str(champion_path),
                **{k: champion_m[k] for k in champion_m if k not in ("model", "regime")},
            }
        ]
    )

    regime_df = pd.DataFrame(regime_rows)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    regime_df.to_csv(config.REGIME_COMPARISON_FILE, index=False)

    error_full = _build_error_analysis_full(
        splits,
        y_test,
        baseline_pred,
        baseline_proba,
        baseline_classes,
        credits_pred,
        credits_proba,
        credits_classes,
    )
    error_full.to_csv(config.ERROR_ANALYSIS_FULL_FILE, index=False)

    case_studies = _build_case_studies(error_full)
    case_studies.to_csv(config.CASE_STUDIES_FILE, index=False)

    n_total = len(splits["df_model"])
    kpis = _build_app_kpis(n_total, len(y_test), champion_m, error_full)
    with config.APP_KPIS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(kpis, fh, indent=2)

    # Backward-compatible slim error analysis (credits model only)
    slim = pd.DataFrame(
        {
            "y_true": error_full["y_true"],
            "y_pred": error_full["y_pred_credits"],
            "confidence": error_full["confidence"],
        }
    )
    for col in error_full.columns:
        if col.startswith("p_") and not col.startswith("base_"):
            slim[col] = error_full[col]
    for col in ("id", "title", "original_title"):
        if col in error_full.columns:
            slim[col] = error_full[col]
    slim.to_csv(config.RESULTS_DIR / "error_analysis.csv", index=False)

    print("\n===== TRAIN_MODELS SUMMARY =====")
    print("Saved champion model:", champion_path)
    print("Saved train artifacts:", config.TRAIN_ARTIFACTS_FILE)
    print("Saved metrics:", config.MODEL_METRICS_FILE)
    print("Saved regime comparison:", config.REGIME_COMPARISON_FILE)
    print("Saved error analysis (full):", config.ERROR_ANALYSIS_FULL_FILE)
    print("Saved case studies:", config.CASE_STUDIES_FILE)
    print("Saved app KPIs:", config.APP_KPIS_FILE)
    print("Saved error analysis (slim):", config.RESULTS_DIR / "error_analysis.csv")
    print("\nRegime comparison (test macro-F1):")
    print(regime_df[["regime", "accuracy", "macro_f1", "f1_flop", "f1_average", "f1_hit"]].to_string(index=False))
    print("\nChampion credits metrics:")
    for k in ("accuracy", "macro_f1", "f1_flop", "f1_average", "f1_hit"):
        print(f"  {k}: {champion_m[k]:.4f}")
    print("\nTransition counts:")
    print(error_full["transition"].value_counts().to_string())
    print("\n", metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()
