#!/usr/bin/env python3
"""Advanced modeling pipeline.

Steps performed (all on the same stratified train/test split from `data.py`):

1. Cross-validation 5-fold of the credits-enriched LR baseline (mean ± std)
2. RandomizedSearchCV hyperparameter tuning for:
     - LogisticRegression
     - RandomForestClassifier
     - GradientBoostingClassifier (sklearn HistGradientBoostingClassifier as well)
     - XGBClassifier (if libomp / xgboost available)
3. Champion selection by CV macro-F1
4. Optional overview LSA features (notebook 04+5 features + 50 LSA dims)
5. Probability calibration via CalibratedClassifierCV(method='isotonic', cv=5)
6. Ordinal cascade: two-step binary models flop-vs-rest + average-vs-hit
7. Reports written to results/ and plots/modeling/

Outputs:
- models/champion_advanced.joblib            ← best calibrated model (full pipeline)
- models/champion_advanced_artifacts.joblib  ← train artifacts incl. overview bundle
- results/cv_results.csv                     ← per-model CV mean ± std
- results/best_hyperparams.json
- results/champion_metrics_advanced.csv
- plots/modeling/30_advanced_cv_macrof1.png
- plots/modeling/31_advanced_reliability_before_after.png
- plots/modeling/32_advanced_ordinal_comparison.png
"""

from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import loguniform, randint, uniform
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    log_loss,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    cross_val_score,
)
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


PLOTS_OUT = config.PLOTS_DIR / "modeling"
RESULTS_OUT = config.RESULTS_DIR
MODELS_OUT = config.MODELS_DIR
PLOTS_OUT.mkdir(parents=True, exist_ok=True)

CV_FOLDS = 5
TUNE_ITER = 25  # randomized search iterations per model
RANDOM_STATE = 42

CLASS_ORDER = ["flop", "average", "hit"]


# ---------------------------------------------------------------------------
# Build modelling matrices (credits regime + optional overview embeddings)
# ---------------------------------------------------------------------------


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
    transformers = []
    if num_cols:
        transformers.append(("num", num_pipe, num_cols))
    if cat_cols:
        transformers.append(("cat", cat_pipe, cat_cols))
    return ColumnTransformer(transformers=transformers)


def _safe_xgb_y(y: pd.Series) -> np.ndarray:
    """XGB expects integer labels."""
    mapping = {c: i for i, c in enumerate(CLASS_ORDER)}
    return np.array([mapping[str(v)] for v in y.values])


# ---------------------------------------------------------------------------
# Step 1 — load splits, add overview LSA features (optional)
# ---------------------------------------------------------------------------


def build_data() -> dict[str, Any]:
    print("[1/7] Building train/test splits (credits regime + overview LSA)…")
    splits = data.load_feature_regime_splits()
    df_model = splits["df_model"]
    idx_train, idx_test = splits["idx_train"], splits["idx_test"]
    y_train, y_test = splits["y_train"], splits["y_test"]
    artifacts = splits["artifacts"]
    credits = splits["credits"]
    credits_features = list(credits["feature_columns"])

    # Re-load raw movies for overview/tagline (the modeling frame already merged credits)
    raw = pd.read_csv(config.PROCESSED_MOVIES_CSV)
    if "overview" not in df_model.columns and "id" in df_model.columns:
        df_model = df_model.merge(raw[["id", "overview", "tagline"]], on="id", how="left")
    text_train = ov.build_text_series(df_model.iloc[idx_train])
    bundle = ov.fit_overview_features(text_train, n_components=50)

    df_with_lsa = ov.attach_overview_features(df_model, bundle)
    lsa_features = bundle.feature_names
    credits_plus_overview = credits_features + lsa_features

    X_train_credits = credits["X_train"]
    X_test_credits = credits["X_test"]
    X_train_full = df_with_lsa.iloc[idx_train][credits_plus_overview].copy()
    X_test_full = df_with_lsa.iloc[idx_test][credits_plus_overview].copy()

    # Stringify categoricals for full-feature set (same contract as data.finalize_credits_X)
    X_train_full = data.finalize_credits_X(X_train_full)
    X_test_full = data.finalize_credits_X(X_test_full)
    num_cols_full, cat_cols_full = data.column_groups_for_credits_pipeline(X_train_full)

    return {
        "y_train": y_train,
        "y_test": y_test,
        "credits_X_train": X_train_credits,
        "credits_X_test": X_test_credits,
        "credits_num_cols": credits["num_cols"],
        "credits_cat_cols": credits["cat_cols"],
        "credits_features": credits_features,
        "overview_bundle": bundle,
        "overview_features": lsa_features,
        "X_train_full": X_train_full,
        "X_test_full": X_test_full,
        "num_cols_full": num_cols_full,
        "cat_cols_full": cat_cols_full,
        "credits_plus_overview": credits_plus_overview,
        "artifacts": artifacts,
        "df_model": df_with_lsa,
    }


# ---------------------------------------------------------------------------
# Step 2 — cross-validation baselines (no tuning)
# ---------------------------------------------------------------------------


def _cv_score(estimator, X, y, label: str) -> dict[str, float]:
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(estimator, X, y, scoring="f1_macro", cv=cv, n_jobs=-1)
    return {
        "model": label,
        "macro_f1_mean": float(scores.mean()),
        "macro_f1_std": float(scores.std()),
        "macro_f1_fold_min": float(scores.min()),
        "macro_f1_fold_max": float(scores.max()),
    }


def cv_baselines(D: dict[str, Any]) -> pd.DataFrame:
    print("[2/7] Cross-validation (5-fold) of base models on credits + overview features…")
    rows: list[dict[str, float]] = []

    prep_credits = _build_preprocessor(D["credits_num_cols"], D["credits_cat_cols"])
    prep_full = _build_preprocessor(D["num_cols_full"], D["cat_cols_full"])

    base_models = [
        ("LogReg credits", prep_credits, D["credits_X_train"], LogisticRegression(max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE, solver="lbfgs")),
        ("LogReg credits + overview", prep_full, D["X_train_full"], LogisticRegression(max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE, solver="lbfgs")),
        ("RandomForest credits", prep_credits, D["credits_X_train"], RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)),
        ("GradientBoosting credits", prep_credits, D["credits_X_train"], GradientBoostingClassifier(random_state=RANDOM_STATE)),
    ]
    if HAS_XGB:
        y_int = _safe_xgb_y(D["y_train"])
        D["y_train_int"] = y_int
        base_models.append(
            (
                "XGBoost credits (default)",
                prep_credits,
                D["credits_X_train"],
                XGBClassifier(
                    n_estimators=300,
                    max_depth=5,
                    learning_rate=0.1,
                    objective="multi:softprob",
                    num_class=3,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    eval_metric="mlogloss",
                    tree_method="hist",
                ),
            )
        )

    for label, prep, X, clf in base_models:
        t0 = time.time()
        pipe = Pipeline([("prep", prep), ("clf", clf)])
        target = D["y_train_int"] if "XGBoost" in label and HAS_XGB else D["y_train"]
        try:
            row = _cv_score(pipe, X, target, label)
        except Exception as exc:
            print(f"  ⚠ {label}: CV failed — {exc}")
            continue
        elapsed = time.time() - t0
        row["elapsed_s"] = round(elapsed, 1)
        rows.append(row)
        print(
            f"  {label:35s}  macro-F1 {row['macro_f1_mean']:.4f} ± {row['macro_f1_std']:.4f}  "
            f"(min {row['macro_f1_fold_min']:.3f}, max {row['macro_f1_fold_max']:.3f}, "
            f"{elapsed:.1f}s)"
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 3 — randomized hyperparameter search
# ---------------------------------------------------------------------------


def _build_search_space() -> list[dict[str, Any]]:
    """Define one RandomizedSearchCV per model family."""

    spaces = [
        {
            "label": "LogReg credits (tuned)",
            "model": LogisticRegression(max_iter=4000, class_weight="balanced", random_state=RANDOM_STATE, solver="lbfgs"),
            "param_distributions": {
                "clf__C": loguniform(1e-2, 10),
            },
            "use_full": False,
        },
        {
            "label": "LogReg credits + overview (tuned)",
            "model": LogisticRegression(max_iter=4000, class_weight="balanced", random_state=RANDOM_STATE, solver="lbfgs"),
            "param_distributions": {
                "clf__C": loguniform(1e-2, 10),
            },
            "use_full": True,
        },
        {
            "label": "RandomForest credits (tuned)",
            "model": RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1),
            "param_distributions": {
                "clf__n_estimators": randint(200, 800),
                "clf__max_depth": randint(4, 16),
                "clf__min_samples_split": randint(2, 12),
                "clf__min_samples_leaf": randint(1, 6),
                "clf__max_features": ["sqrt", "log2", 0.5],
            },
            "use_full": False,
        },
        {
            "label": "GradientBoosting credits (tuned)",
            "model": GradientBoostingClassifier(random_state=RANDOM_STATE),
            "param_distributions": {
                "clf__n_estimators": randint(150, 500),
                "clf__max_depth": randint(2, 6),
                "clf__learning_rate": loguniform(0.01, 0.2),
                "clf__subsample": uniform(0.7, 0.3),
            },
            "use_full": False,
        },
    ]
    if HAS_XGB:
        spaces.append(
            {
                "label": "XGBoost credits (tuned)",
                "model": XGBClassifier(
                    objective="multi:softprob",
                    num_class=3,
                    random_state=RANDOM_STATE,
                    n_jobs=-1,
                    eval_metric="mlogloss",
                    tree_method="hist",
                ),
                "param_distributions": {
                    "clf__n_estimators": randint(150, 500),
                    "clf__max_depth": randint(3, 8),
                    "clf__learning_rate": loguniform(0.02, 0.25),
                    "clf__subsample": uniform(0.7, 0.3),
                    "clf__colsample_bytree": uniform(0.6, 0.4),
                    "clf__reg_lambda": loguniform(1e-3, 5),
                    "clf__min_child_weight": randint(1, 8),
                },
                "use_full": False,
                "xgb": True,
            }
        )
    return spaces


def randomized_tuning(D: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    print(f"[3/7] RandomizedSearchCV ({TUNE_ITER} iters, 5-fold) for {len(_build_search_space())} model families…")
    rows: list[dict[str, Any]] = []
    best_params: dict[str, Any] = {}
    fitted_estimators: dict[str, Pipeline] = {}

    prep_credits = _build_preprocessor(D["credits_num_cols"], D["credits_cat_cols"])
    prep_full = _build_preprocessor(D["num_cols_full"], D["cat_cols_full"])

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    for space in _build_search_space():
        label = space["label"]
        if space["use_full"]:
            X, prep = D["X_train_full"], prep_full
        else:
            X, prep = D["credits_X_train"], prep_credits

        target = D["y_train"]
        if space.get("xgb"):
            target = D.get("y_train_int", _safe_xgb_y(D["y_train"]))

        pipe = Pipeline([("prep", prep), ("clf", space["model"])])

        search = RandomizedSearchCV(
            pipe,
            param_distributions=space["param_distributions"],
            n_iter=TUNE_ITER,
            scoring="f1_macro",
            cv=cv,
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbose=0,
            return_train_score=False,
        )
        t0 = time.time()
        try:
            search.fit(X, target)
        except Exception as exc:
            print(f"  ⚠ {label}: tuning failed — {exc}")
            continue
        elapsed = time.time() - t0

        rows.append(
            {
                "model": label,
                "macro_f1_mean": float(search.best_score_),
                "macro_f1_std": float(search.cv_results_["std_test_score"][search.best_index_]),
                "best_params": {k.replace("clf__", ""): v for k, v in search.best_params_.items()},
                "elapsed_s": round(elapsed, 1),
            }
        )
        best_params[label] = rows[-1]["best_params"]
        fitted_estimators[label] = search.best_estimator_
        print(
            f"  {label:40s}  best macro-F1 {search.best_score_:.4f} ± "
            f"{rows[-1]['macro_f1_std']:.4f}  ({elapsed:.1f}s)"
        )

    return pd.DataFrame(rows), best_params, fitted_estimators


# ---------------------------------------------------------------------------
# Step 4 — champion selection + calibration
# ---------------------------------------------------------------------------


def select_champion(
    tuned_df: pd.DataFrame, fitted: dict[str, Pipeline]
) -> tuple[str, Pipeline]:
    print("[4/7] Selecting champion by CV macro-F1…")
    if tuned_df.empty:
        raise RuntimeError("No tuned models available.")
    top = tuned_df.sort_values("macro_f1_mean", ascending=False).iloc[0]
    label = str(top["model"])
    print(f"  Champion: {label} (macro-F1 {top['macro_f1_mean']:.4f} ± {top['macro_f1_std']:.4f})")
    return label, fitted[label]


def _estimator_classes(estimator) -> list:
    """Return the class labels stored on an arbitrary fitted estimator."""
    classes = getattr(estimator, "classes_", None)
    if classes is None and hasattr(estimator, "named_steps") and "clf" in estimator.named_steps:
        classes = estimator.named_steps["clf"].classes_
    return list(classes) if classes is not None else CLASS_ORDER


def evaluate_on_test(name: str, estimator, X_test, y_test, use_int: bool = False) -> dict[str, float]:
    classes = _estimator_classes(estimator)
    if use_int:
        y_true = _safe_xgb_y(y_test)
        y_pred_raw = estimator.predict(X_test)
        # raw labels from this estimator are integer indices (0/1/2)
        if classes and not isinstance(classes[0], (int, np.integer)):
            # CalibratedClassifierCV may return ints; map back to strings
            try:
                y_pred = np.array([CLASS_ORDER[int(v)] for v in y_pred_raw])
            except (ValueError, IndexError):
                y_pred = y_pred_raw
        else:
            y_pred = np.array([CLASS_ORDER[int(v)] for v in y_pred_raw])
        y_proba = estimator.predict_proba(X_test)
        ll = log_loss(y_true, y_proba, labels=list(range(3)))
    else:
        y_pred = estimator.predict(X_test)
        y_proba = estimator.predict_proba(X_test)
        try:
            ll = log_loss(y_test, y_proba, labels=classes)
        except Exception:
            ll = float("nan")
    macro = f1_score(y_test, y_pred, average="macro")
    acc = accuracy_score(y_test, y_pred)
    print(f"  {name:45s} accuracy {acc:.4f}  macro-F1 {macro:.4f}  log-loss {ll:.4f}")
    rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    return {
        "name": name,
        "accuracy": acc,
        "macro_f1": macro,
        "log_loss": ll,
        "f1_flop": rep.get("flop", {}).get("f1-score", 0.0),
        "f1_average": rep.get("average", {}).get("f1-score", 0.0),
        "f1_hit": rep.get("hit", {}).get("f1-score", 0.0),
    }


def calibrate_champion(label: str, champion_pipe, D: dict[str, Any]):
    print("[5/7] Probability calibration (isotonic, 5-fold)…")
    if "XGBoost" in label:
        # XGBClassifier needs integer y inside CalibratedClassifierCV
        use_full = False
        X = D["credits_X_train"]
        y = D.get("y_train_int", _safe_xgb_y(D["y_train"]))
    else:
        use_full = "overview" in label
        X = D["X_train_full"] if use_full else D["credits_X_train"]
        y = D["y_train"]

    # ``CalibratedClassifierCV`` will refit on each fold using cv=5 → so we
    # wrap the *unfitted* pipeline with the best params already baked in.
    calibrated = CalibratedClassifierCV(champion_pipe, method="isotonic", cv=5)
    t0 = time.time()
    calibrated.fit(X, y)
    print(f"  Calibration fitted in {time.time() - t0:.1f}s")
    return calibrated, use_full, "XGBoost" in label


# ---------------------------------------------------------------------------
# Step 6 — ordinal cascade comparison
# ---------------------------------------------------------------------------


def ordinal_cascade(D: dict[str, Any]) -> dict[str, Any]:
    """Two-step ordinal cascade: P(flop) then P(hit | not_flop).

    Compared against the multinomial credits LR baseline on the same test set.
    """

    print("[6/7] Ordinal cascade (flop vs not-flop → hit vs average)…")
    y_train, y_test = D["y_train"], D["y_test"]
    X_train, X_test = D["credits_X_train"], D["credits_X_test"]
    prep = _build_preprocessor(D["credits_num_cols"], D["credits_cat_cols"])

    is_flop_train = (y_train == "flop").astype(int)
    pipe_flop = Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE))])
    pipe_flop.fit(X_train, is_flop_train)
    p_flop = pipe_flop.predict_proba(X_test)[:, 1]

    mask_notflop = y_train != "flop"
    X_train_nf = X_train[mask_notflop.values] if hasattr(X_train, "loc") else X_train[mask_notflop]
    y_train_nf = y_train[mask_notflop]
    is_hit_train = (y_train_nf == "hit").astype(int)
    prep_nf = _build_preprocessor(D["credits_num_cols"], D["credits_cat_cols"])
    pipe_hit = Pipeline([("prep", prep_nf), ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE))])
    pipe_hit.fit(X_train_nf, is_hit_train)
    p_hit_given_nf = pipe_hit.predict_proba(X_test)[:, 1]

    p_avg = (1 - p_flop) * (1 - p_hit_given_nf)
    p_hit = (1 - p_flop) * p_hit_given_nf
    probas = np.stack([p_flop, p_avg, p_hit], axis=1)
    classes = ["flop", "average", "hit"]
    y_pred = np.array([classes[int(np.argmax(row))] for row in probas])

    macro = f1_score(y_test, y_pred, average="macro")
    acc = accuracy_score(y_test, y_pred)
    rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    print(f"  Ordinal cascade   accuracy {acc:.4f}  macro-F1 {macro:.4f}")
    return {
        "name": "Ordinal cascade (flop → hit|not_flop)",
        "accuracy": acc,
        "macro_f1": macro,
        "f1_flop": rep.get("flop", {}).get("f1-score", 0.0),
        "f1_average": rep.get("average", {}).get("f1-score", 0.0),
        "f1_hit": rep.get("hit", {}).get("f1-score", 0.0),
    }


# ---------------------------------------------------------------------------
# Step 7 — plots & persistence
# ---------------------------------------------------------------------------


def plot_cv_results(cv_df: pd.DataFrame, tuned_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    all_rows = pd.concat([cv_df.assign(kind="baseline"), tuned_df.assign(kind="tuned")], ignore_index=True)
    all_rows = all_rows.sort_values("macro_f1_mean", ascending=True)
    colors = ["#94A3B8" if k == "baseline" else "#2563EB" for k in all_rows["kind"].tolist()]
    ax.barh(all_rows["model"], all_rows["macro_f1_mean"], xerr=all_rows.get("macro_f1_std", 0), color=colors)
    ax.set_xlabel("CV macro-F1 (mean ± std, 5-fold)")
    ax.set_title("Cross-validation macro-F1 — baselines vs tuned")
    ax.axvline(all_rows["macro_f1_mean"].max(), color="#15803D", linestyle="--", linewidth=1, alpha=0.6)
    plt.tight_layout()
    out = PLOTS_OUT / "30_advanced_cv_macrof1.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ↳ {out.relative_to(ROOT)}")


def plot_reliability(
    y_test, proba_before, classes_before, proba_after, classes_after, n_bins: int = 10
) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    for label, proba, classes, color in [
        ("Before calibration", proba_before, classes_before, "#9CA3AF"),
        ("After (isotonic)", proba_after, classes_after, "#2563EB"),
    ]:
        # multiclass reliability: take max-prob class confidence vs correctness
        argmax = np.argmax(proba, axis=1)
        if isinstance(classes[0], (int, np.integer)):
            preds = np.array([CLASS_ORDER[i] for i in argmax])
        else:
            preds = np.array([classes[i] for i in argmax])
        conf = proba.max(axis=1)
        correct = (preds == y_test.values).astype(int)
        bins = np.linspace(0, 1, n_bins + 1)
        binned_conf = []
        binned_acc = []
        for i in range(n_bins):
            mask = (conf >= bins[i]) & (conf < bins[i + 1])
            if mask.sum() == 0:
                continue
            binned_conf.append(conf[mask].mean())
            binned_acc.append(correct[mask].mean())
        ax.plot(binned_conf, binned_acc, marker="o", label=label, color=color)
    ax.plot([0, 1], [0, 1], linestyle="--", color="#CBD5E1", label="Perfect calibration")
    ax.set_xlabel("Confidence (max predicted probability)")
    ax.set_ylabel("Empirical accuracy")
    ax.set_title("Reliability — before vs after isotonic calibration")
    ax.legend()
    ax.grid(alpha=0.2)
    plt.tight_layout()
    out = PLOTS_OUT / "31_advanced_reliability_before_after.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ↳ {out.relative_to(ROOT)}")


def plot_ordinal_comparison(metrics_rows: list[dict[str, float]]) -> None:
    df = pd.DataFrame(metrics_rows)
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    df_sorted = df.sort_values("macro_f1", ascending=True)
    ax.barh(df_sorted["name"], df_sorted["macro_f1"], color="#2563EB")
    for i, (_, row) in enumerate(df_sorted.iterrows()):
        ax.text(row["macro_f1"] + 0.005, i, f"{row['macro_f1']:.3f}", va="center", fontsize=9)
    ax.set_xlabel("Test macro-F1")
    ax.set_title("Test macro-F1 — champion variants")
    ax.set_xlim(0, max(df["macro_f1"].max() + 0.05, 0.55))
    plt.tight_layout()
    out = PLOTS_OUT / "32_advanced_ordinal_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  ↳ {out.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"XGBoost available: {HAS_XGB}")
    D = build_data()

    cv_df = cv_baselines(D)

    tuned_df, best_params, fitted = randomized_tuning(D)

    champion_label, champion_pipe = select_champion(tuned_df, fitted)

    print("Evaluating uncalibrated tuned models on test set…")
    test_rows: list[dict[str, float]] = []
    for label, est in fitted.items():
        use_int = "XGBoost" in label
        use_full = "overview" in label
        X_te = D["X_test_full"] if use_full else D["credits_X_test"]
        test_rows.append(evaluate_on_test(label, est, X_te, D["y_test"], use_int=use_int))

    calibrated, used_full, used_int = calibrate_champion(champion_label, champion_pipe, D)
    X_te = D["X_test_full"] if used_full else D["credits_X_test"]
    cal_row = evaluate_on_test(f"{champion_label} + isotonic calibration", calibrated, X_te, D["y_test"], use_int=used_int)
    test_rows.append(cal_row)

    ord_row = ordinal_cascade(D)
    test_rows.append(ord_row)

    # --- Reliability plot (before/after calibration) ---
    proba_before = champion_pipe.predict_proba(X_te)
    classes_before = _estimator_classes(champion_pipe)
    proba_after = calibrated.predict_proba(X_te)
    classes_after = _estimator_classes(calibrated)
    plot_reliability(D["y_test"], proba_before, classes_before, proba_after, classes_after)

    plot_cv_results(cv_df, tuned_df)
    plot_ordinal_comparison(test_rows)

    # --- Persist artifacts ---
    print("[7/7] Persisting champion model + reports…")
    bundle = {
        "model": calibrated,
        "champion_label": champion_label,
        "used_full_features": used_full,
        "used_int_labels": used_int,
        "feature_columns": D["credits_plus_overview"] if used_full else D["credits_features"],
        "credits_features": D["credits_features"],
        "overview_features": D["overview_features"],
    }
    joblib.dump(bundle, MODELS_OUT / "champion_advanced.joblib")

    full_artifacts = dict(D["artifacts"])
    full_artifacts["overview_bundle"] = D["overview_bundle"]
    full_artifacts["overview_features"] = D["overview_features"]
    full_artifacts["credits_plus_overview"] = D["credits_plus_overview"]
    joblib.dump(full_artifacts, MODELS_OUT / "champion_advanced_artifacts.joblib")

    cv_df.to_csv(RESULTS_OUT / "cv_baselines.csv", index=False)
    tuned_df.assign(best_params=tuned_df["best_params"].apply(json.dumps)).to_csv(
        RESULTS_OUT / "cv_tuned.csv", index=False
    )

    with (RESULTS_OUT / "best_hyperparams.json").open("w", encoding="utf-8") as fh:
        json.dump({k: {kk: float(vv) if hasattr(vv, "item") else vv for kk, vv in v.items()} for k, v in best_params.items()}, fh, indent=2, default=str)

    metrics_out = pd.DataFrame(test_rows)
    metrics_out.to_csv(RESULTS_OUT / "champion_metrics_advanced.csv", index=False)

    print("\n===== ADVANCED MODELING SUMMARY =====")
    print(f"CV baselines:\n{cv_df.to_string(index=False)}\n")
    print(f"Tuned models:\n{tuned_df.drop(columns=['best_params']).to_string(index=False)}\n")
    print(f"Test-set metrics:\n{metrics_out.to_string(index=False)}\n")
    print(f"Champion: {champion_label}")
    print("Saved:")
    print(f"  - {MODELS_OUT / 'champion_advanced.joblib'}")
    print(f"  - {MODELS_OUT / 'champion_advanced_artifacts.joblib'}")
    print(f"  - {RESULTS_OUT / 'cv_baselines.csv'}")
    print(f"  - {RESULTS_OUT / 'cv_tuned.csv'}")
    print(f"  - {RESULTS_OUT / 'best_hyperparams.json'}")
    print(f"  - {RESULTS_OUT / 'champion_metrics_advanced.csv'}")


if __name__ == "__main__":
    main()
