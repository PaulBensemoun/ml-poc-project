#!/usr/bin/env python3
"""Refit every tuned model with its best hyperparameters and persist each one.

This script reuses `results/best_hyperparams.json` produced by
`scripts/advanced_modeling.py`, so it avoids running RandomizedSearchCV
again. It writes:

  models/champion_<slug>.joblib   ← every variant (LR, RF, GB, XGB, LR+overview)
  models/production_champion.joblib       ← best test macro-F1 model
  models/production_champion_calibrated.joblib   ← calibrated for app probabilities
  models/production_champion_meta.json    ← which model wins, why
  results/production_test_metrics.json    ← final headline metrics
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import config
import data
import overview_features as ov

try:
    from xgboost import XGBClassifier  # type: ignore
    HAS_XGB = True
except Exception:
    XGBClassifier = None  # type: ignore
    HAS_XGB = False


CLASS_ORDER = ["flop", "average", "hit"]
RANDOM_STATE = 42


def _build_preprocessor(num_cols: list[str], cat_cols: list[str]) -> ColumnTransformer:
    num_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())])
    cat_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    tr = []
    if num_cols:
        tr.append(("num", num_pipe, num_cols))
    if cat_cols:
        tr.append(("cat", cat_pipe, cat_cols))
    return ColumnTransformer(transformers=tr)


def _y_int(y: pd.Series) -> np.ndarray:
    m = {c: i for i, c in enumerate(CLASS_ORDER)}
    return np.array([m[str(v)] for v in y.values])


def _build_data() -> dict:
    splits = data.load_feature_regime_splits()
    df_model = splits["df_model"]
    idx_train, idx_test = splits["idx_train"], splits["idx_test"]
    y_train, y_test = splits["y_train"], splits["y_test"]
    credits = splits["credits"]
    credits_features = list(credits["feature_columns"])

    raw = pd.read_csv(config.PROCESSED_MOVIES_CSV)
    if "overview" not in df_model.columns and "id" in df_model.columns:
        df_model = df_model.merge(raw[["id", "overview", "tagline"]], on="id", how="left")
    text_train = ov.build_text_series(df_model.iloc[idx_train])
    bundle = ov.fit_overview_features(text_train, n_components=50)
    df_with_lsa = ov.attach_overview_features(df_model, bundle)
    lsa_features = bundle.feature_names

    full_features = credits_features + lsa_features
    X_train_full = data.finalize_credits_X(df_with_lsa.iloc[idx_train][full_features].copy())
    X_test_full = data.finalize_credits_X(df_with_lsa.iloc[idx_test][full_features].copy())
    num_cols_full, cat_cols_full = data.column_groups_for_credits_pipeline(X_train_full)

    return {
        "y_train": y_train,
        "y_test": y_test,
        "X_train_credits": credits["X_train"],
        "X_test_credits": credits["X_test"],
        "credits_num_cols": credits["num_cols"],
        "credits_cat_cols": credits["cat_cols"],
        "X_train_full": X_train_full,
        "X_test_full": X_test_full,
        "num_cols_full": num_cols_full,
        "cat_cols_full": cat_cols_full,
        "overview_bundle": bundle,
        "credits_features": credits_features,
        "full_features": full_features,
        "lsa_features": lsa_features,
        "artifacts": splits["artifacts"],
        "splits": splits,
    }


def _build_model(label: str, best_params: dict, num_cols: list[str], cat_cols: list[str]):
    prep = _build_preprocessor(num_cols, cat_cols)
    if "LogReg" in label:
        clf = LogisticRegression(
            max_iter=4000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            solver="lbfgs",
            **{k: v for k, v in best_params.items() if k in ("C",)},
        )
    elif "RandomForest" in label:
        clf = RandomForestClassifier(
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
            **best_params,
        )
    elif "GradientBoosting" in label:
        clf = GradientBoostingClassifier(random_state=RANDOM_STATE, **best_params)
    elif "XGBoost" in label and HAS_XGB:
        clf = XGBClassifier(
            objective="multi:softprob",
            num_class=3,
            random_state=RANDOM_STATE,
            n_jobs=-1,
            eval_metric="mlogloss",
            tree_method="hist",
            **best_params,
        )
    else:
        return None
    return Pipeline([("prep", prep), ("clf", clf)])


def _slug(label: str) -> str:
    return (
        label.lower()
        .replace(" credits (tuned)", "_tuned")
        .replace(" credits + overview (tuned)", "_overview_tuned")
        .replace("logreg", "logreg")
        .replace("randomforest", "rf")
        .replace("gradientboosting", "gb")
        .replace("xgboost", "xgb")
        .replace(" ", "_")
    )


def _eval_pipeline(name: str, pipe, X_test, y_test, use_int: bool = False) -> dict:
    if use_int:
        y_true_int = _y_int(y_test)
        y_pred_int = pipe.predict(X_test)
        y_pred = np.array([CLASS_ORDER[int(v)] for v in y_pred_int])
        proba = pipe.predict_proba(X_test)
        ll = log_loss(y_true_int, proba, labels=list(range(3)))
    else:
        y_pred = pipe.predict(X_test)
        proba = pipe.predict_proba(X_test)
        try:
            ll = log_loss(y_test, proba, labels=list(pipe.named_steps["clf"].classes_))
        except Exception:
            ll = float("nan")
    rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    return {
        "name": name,
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "macro_f1": float(f1_score(y_test, y_pred, average="macro")),
        "log_loss": float(ll),
        "f1_flop": rep.get("flop", {}).get("f1-score", 0.0),
        "f1_average": rep.get("average", {}).get("f1-score", 0.0),
        "f1_hit": rep.get("hit", {}).get("f1-score", 0.0),
    }


def main() -> None:
    best_path = config.RESULTS_DIR / "best_hyperparams.json"
    if not best_path.exists():
        raise SystemExit("Missing results/best_hyperparams.json — run scripts/advanced_modeling.py first.")
    best_params = json.loads(best_path.read_text())

    D = _build_data()

    refitted: dict[str, dict] = {}
    metrics_rows = []

    for label, params in best_params.items():
        use_full = "overview" in label
        use_int = "XGBoost" in label
        num_cols = D["num_cols_full"] if use_full else D["credits_num_cols"]
        cat_cols = D["cat_cols_full"] if use_full else D["credits_cat_cols"]
        X_train = D["X_train_full"] if use_full else D["X_train_credits"]
        X_test = D["X_test_full"] if use_full else D["X_test_credits"]
        y_train = _y_int(D["y_train"]) if use_int else D["y_train"]

        pipe = _build_model(label, {k: v for k, v in params.items()}, num_cols, cat_cols)
        if pipe is None:
            continue
        pipe.fit(X_train, y_train)

        slug = _slug(label)
        out_path = config.MODELS_DIR / f"champion_{slug}.joblib"
        joblib.dump(
            {
                "pipeline": pipe,
                "label": label,
                "use_full_features": use_full,
                "use_int_labels": use_int,
                "feature_columns": D["full_features"] if use_full else D["credits_features"],
            },
            out_path,
        )
        m = _eval_pipeline(label, pipe, X_test, D["y_test"], use_int=use_int)
        metrics_rows.append(m)
        refitted[label] = {"pipeline": pipe, "metrics": m, "use_full": use_full, "use_int": use_int}
        print(f"✓ {label:38s}  acc {m['accuracy']:.4f}  macro-F1 {m['macro_f1']:.4f}  → {out_path.name}")

    if not refitted:
        raise SystemExit("No models refitted.")

    # --- Pick the production champion: best test macro-F1 (ignore XGB int labelling)
    candidates = {k: v for k, v in refitted.items() if not v["use_int"]}
    if not candidates:
        candidates = refitted
    champion_label = max(candidates, key=lambda k: candidates[k]["metrics"]["macro_f1"])
    champion = candidates[champion_label]

    # Save the production champion (uncalibrated, for macro-F1 narrative)
    production_path = config.MODELS_DIR / "production_champion.joblib"
    joblib.dump(
        {
            "pipeline": champion["pipeline"],
            "label": champion_label,
            "use_full_features": champion["use_full"],
            "use_int_labels": champion["use_int"],
            "feature_columns": D["full_features"] if champion["use_full"] else D["credits_features"],
        },
        production_path,
    )

    # Fit + save a calibrated wrapper (for app probabilities / log-loss)
    X_train = D["X_train_full"] if champion["use_full"] else D["X_train_credits"]
    y_train = D["y_train"]
    cal = CalibratedClassifierCV(champion["pipeline"], method="isotonic", cv=5)
    cal.fit(X_train, y_train)
    X_test = D["X_test_full"] if champion["use_full"] else D["X_test_credits"]
    m_cal = _eval_pipeline(champion_label + " + isotonic calibration", cal, X_test, D["y_test"], use_int=False)
    metrics_rows.append(m_cal)
    calibrated_path = config.MODELS_DIR / "production_champion_calibrated.joblib"
    joblib.dump(
        {
            "pipeline": cal,
            "label": champion_label + " + isotonic calibration",
            "use_full_features": champion["use_full"],
            "use_int_labels": False,
            "feature_columns": D["full_features"] if champion["use_full"] else D["credits_features"],
        },
        calibrated_path,
    )

    # Persist artifacts (incl. overview bundle for inference if needed)
    full_artifacts = dict(D["artifacts"])
    full_artifacts["overview_bundle"] = D["overview_bundle"]
    full_artifacts["overview_features"] = D["lsa_features"]
    full_artifacts["full_features"] = D["full_features"]
    joblib.dump(full_artifacts, config.MODELS_DIR / "production_champion_artifacts.joblib")

    # Meta + final metrics
    meta = {
        "champion_label": champion_label,
        "use_full_features": champion["use_full"],
        "selection_criterion": "best test macro-F1 among LR/RF/GB variants",
        "calibrated_variant": calibrated_path.name,
    }
    (config.MODELS_DIR / "production_champion_meta.json").write_text(json.dumps(meta, indent=2))
    pd.DataFrame(metrics_rows).to_csv(config.RESULTS_DIR / "production_test_metrics.csv", index=False)

    print(f"\nProduction champion: {champion_label}")
    print(f"  Saved: {production_path.name}, {calibrated_path.name}")
    print(f"  Artifacts: production_champion_artifacts.joblib")
    print(f"  Test metrics: macro-F1 {champion['metrics']['macro_f1']:.4f}  acc {champion['metrics']['accuracy']:.4f}")
    print(f"  + calibrated: macro-F1 {m_cal['macro_f1']:.4f}  acc {m_cal['accuracy']:.4f}")
    print()
    print(pd.DataFrame(metrics_rows).to_string(index=False))


if __name__ == "__main__":
    main()
