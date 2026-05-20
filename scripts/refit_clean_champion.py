#!/usr/bin/env python3
"""Refit the production champion (tuned LR) with a *cleaned* feature set.

The original training kept several redundant features that produced a
multicollinear logistic regression — for example:

  • ``budget`` and ``budget_log`` are monotonic transforms of each other
    (Spearman r = 1.0). With L2-regularized LR, the two features end up
    with OPPOSING coefficients (+0.110 for raw budget, -0.270 for
    log-budget on the HIT class). Net effect: increasing the user-input
    budget *decreases* the HIT probability slightly — a clearly
    counter-intuitive sensitivity signal for a commercial product.
  • ``release_month`` (categorical), ``release_quarter`` (categorical) and
    ``release_season`` (categorical) are all derived from the same
    underlying signal → triple one-hot encoding of the same information.
  • ``director_bucket`` produces 26 one-hot columns trained on 8–23 films
    each, which is far too few for stable per-director coefficients
    (e.g. Spielberg ends up with a negative HIT coefficient). The
    aggregate signals ``top_director_flag`` + ``director_movie_count``
    already capture the relevant group-level information.

This script keeps the existing CV / hyper-parameter search results, drops
the noisy/redundant columns, refits the tuned LR, and writes a new
production champion + artifacts. The previous artefacts remain available
in git history. The original ``scripts/refit_champions.py`` is *not*
modified, so the notebook narrative remains valid.
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
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import config
import data


# Features we drop because they are redundant / overfit. The dropped column
# stays in the artifacts table (so the inference layer can still receive
# user inputs for them) — we just skip them at training time.
REDUNDANT_NUMERIC = ["budget"]  # keep only budget_log
REDUNDANT_CATEGORICAL = [
    "release_quarter",   # derived from release_month
    "release_season",    # derived from release_month
    "director_bucket",   # 26 categories × 8–23 films each → overfit; keep top_director_flag + director_movie_count + talent_score
]


CLASS_ORDER = ["flop", "average", "hit"]
RANDOM_STATE = 42


def _build_preprocessor(num_cols: list[str], cat_cols: list[str]) -> ColumnTransformer:
    num_pipe = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
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


def _eval(name: str, pipe, X_test, y_test) -> dict:
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
    print("=" * 70)
    print("Refit clean champion (LR, cleaned feature set)")
    print("=" * 70)

    # Reuse best LR hyperparameters
    best_path = config.RESULTS_DIR / "best_hyperparams.json"
    best_params = json.loads(best_path.read_text())
    lr_label = next(
        (label for label in best_params if "LogReg" in label and "overview" not in label),
        None,
    )
    if lr_label is None:
        raise SystemExit("No tuned LogReg in best_hyperparams.json")
    lr_C = float(best_params[lr_label].get("C", 1.0))
    print(f"Reusing tuned LR hyperparameters from '{lr_label}'  →  C={lr_C:.4f}")

    # Build full data the same way the original script does
    splits = data.load_feature_regime_splits()
    credits = splits["credits"]
    X_train = credits["X_train"].copy()
    X_test = credits["X_test"].copy()
    y_train, y_test = splits["y_train"], splits["y_test"]
    print(f"Train: {X_train.shape}  Test: {X_test.shape}")

    # Drop redundant columns from BOTH train and test
    cols_to_drop = [c for c in (REDUNDANT_NUMERIC + REDUNDANT_CATEGORICAL) if c in X_train.columns]
    X_train_clean = X_train.drop(columns=cols_to_drop)
    X_test_clean = X_test.drop(columns=cols_to_drop)
    print(f"Dropped {len(cols_to_drop)} redundant features: {cols_to_drop}")
    print(f"Clean train: {X_train_clean.shape}  Clean test: {X_test_clean.shape}")

    num_cols_clean, cat_cols_clean = data.column_groups_for_credits_pipeline(X_train_clean)
    print(f"Clean numeric columns ({len(num_cols_clean)}): {num_cols_clean}")
    print(f"Clean categorical columns ({len(cat_cols_clean)}): {cat_cols_clean}")

    # Build + fit
    prep = _build_preprocessor(num_cols_clean, cat_cols_clean)
    clf = LogisticRegression(
        max_iter=4000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        solver="lbfgs",
        C=lr_C,
    )
    pipe = Pipeline([("prep", prep), ("clf", clf)])
    pipe.fit(X_train_clean, y_train)

    # Evaluate
    m_clean = _eval("LR clean (no redundant)", pipe, X_test_clean, y_test)
    print(f"\n=== CLEAN model metrics ===")
    print(f"  Accuracy : {m_clean['accuracy']:.4f}")
    print(f"  Macro-F1 : {m_clean['macro_f1']:.4f}")
    print(f"  Log-loss : {m_clean['log_loss']:.4f}")
    print(f"  F1 per class: flop {m_clean['f1_flop']:.3f}  avg {m_clean['f1_average']:.3f}  hit {m_clean['f1_hit']:.3f}")

    # Inspect the new budget_log coefficient — should now be cleanly positive or negative
    feat_names = pipe.named_steps["prep"].get_feature_names_out()
    coefs = pd.DataFrame(pipe.named_steps["clf"].coef_.T, index=feat_names, columns=pipe.named_steps["clf"].classes_)
    print("\n=== Sanity check — budget_log coefficients (should be a single coherent sign) ===")
    print(coefs[coefs.index.str.contains("budget")].round(3))

    # Compare against existing production champion
    existing = config.MODELS_DIR / "production_champion.joblib"
    if existing.exists():
        old = joblib.load(existing)
        old_pipe = old["pipeline"]
        m_old = _eval("LR original (with redundant)", old_pipe, X_test, y_test)
        print(f"\n=== OLD production champion metrics (for comparison) ===")
        print(f"  Accuracy : {m_old['accuracy']:.4f}")
        print(f"  Macro-F1 : {m_old['macro_f1']:.4f}")
        delta_f1 = m_clean["macro_f1"] - m_old["macro_f1"]
        delta_acc = m_clean["accuracy"] - m_old["accuracy"]
        print(f"  Δ macro-F1: {delta_f1:+.4f}   Δ accuracy: {delta_acc:+.4f}")

    # Persist
    production_path = config.MODELS_DIR / "production_champion.joblib"
    feature_columns_clean = list(X_train_clean.columns)
    joblib.dump(
        {
            "pipeline": pipe,
            "label": lr_label + " — cleaned feature set",
            "use_full_features": False,
            "use_int_labels": False,
            "feature_columns": feature_columns_clean,
        },
        production_path,
    )
    print(f"\n✓ Wrote {production_path}")

    # Update the artifacts: trim credits_features / numeric_columns / categorical_columns
    art = dict(splits["artifacts"])
    art["credits_features"] = feature_columns_clean
    art["numeric_columns"] = num_cols_clean
    art["categorical_columns"] = cat_cols_clean
    # Drop overview bundle if present so inference doesn't try to attach LSA cols
    art.pop("overview_bundle", None)
    art.pop("overview_features", None)
    art.pop("full_features", None)
    artifacts_path = config.MODELS_DIR / "production_champion_artifacts.joblib"
    joblib.dump(art, artifacts_path)
    print(f"✓ Wrote {artifacts_path}")

    # Meta
    meta = {
        "champion_label": lr_label + " — cleaned feature set",
        "use_full_features": False,
        "selection_criterion": (
            "Refit with cleaned feature set (dropped duplicate budget / "
            "release_quarter / release_season / director_bucket) to remove "
            "multicollinearity in the LR coefficients."
        ),
        "dropped_features": cols_to_drop,
        "final_features": feature_columns_clean,
    }
    (config.MODELS_DIR / "production_champion_meta.json").write_text(json.dumps(meta, indent=2))

    # Update final metrics CSV
    pd.DataFrame([m_clean]).to_csv(
        config.RESULTS_DIR / "production_test_metrics_clean.csv", index=False
    )

    # Update app_kpis.json
    kpis_path = config.RESULTS_DIR / "app_kpis.json"
    if kpis_path.exists():
        kpis = json.loads(kpis_path.read_text())
    else:
        kpis = {}
    kpis["champion_macro_f1"] = m_clean["macro_f1"]
    kpis["champion_accuracy"] = m_clean["accuracy"]
    kpis["champion_log_loss"] = m_clean["log_loss"]
    kpis["champion_f1_flop"] = m_clean["f1_flop"]
    kpis["champion_f1_average"] = m_clean["f1_average"]
    kpis["champion_f1_hit"] = m_clean["f1_hit"]
    kpis_path.write_text(json.dumps(kpis, indent=2))
    print(f"✓ Updated {kpis_path}")


if __name__ == "__main__":
    main()
