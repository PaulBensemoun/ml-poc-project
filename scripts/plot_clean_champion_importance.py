#!/usr/bin/env python3
"""Generate a feature-importance plot for the *clean* production champion.

This uses **permutation importance** (sklearn ``permutation_importance``)
with ``scoring='f1_macro'`` on the held-out test set. Each of the 25 source
features is permuted ``n_repeats`` times; the importance is the mean drop
in macro-F1 caused by that permutation.

Why permutation importance instead of raw |coef|?
  * The previous version summed ``|coef|`` across one-hot dummies, which
    mechanically inflated high-cardinality categorical features (e.g.
    ``original_language`` has ~40 dummies, ``budget_log`` has 1). The
    resulting ranking did not reflect actual model behaviour.
  * Permutation importance operates on the *source* column, so a feature
    encoded as 40 dummies and a feature encoded as 1 float are compared
    on the same scale: how much does macro-F1 drop when we destroy that
    column's information?

Output: ``plots/modeling/30_clean_champion_feature_importance.png``
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import config  # noqa: E402
import data as data_mod  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

OUTPUT = config.PLOTS_DIR / "modeling" / "30_clean_champion_feature_importance.png"
N_REPEATS = 30
RANDOM_STATE = 42

DROPPED = ["budget", "release_quarter", "release_season", "director_bucket"]

# Human-readable labels for the plot axes
PRETTY = {
    "budget_log": "budget (log)",
    "runtime": "durée (min)",
    "runtime_bucket": "durée (bucket)",
    "main_genre": "genre principal",
    "genre_count": "nombre de genres",
    "genre_complexity": "complexité du genre",
    "original_language": "langue d'origine",
    "spoken_language_count": "langues parlées (nb)",
    "multilingual_movie": "film multilingue",
    "production_company_count": "sociétés de production",
    "production_country_count": "pays de production",
    "international_production": "production internationale",
    "production_scale": "échelle de production",
    "decade": "décennie",
    "release_month": "mois de sortie",
    "cast_size": "taille du cast",
    "top_billed_cast_count": "têtes d'affiche",
    "known_actor_count": "acteurs connus",
    "ensemble_cast_flag": "cast ensemble",
    "crew_size": "taille de l'équipe",
    "writer_count": "scénaristes",
    "director_movie_count": "films du réalisateur",
    "top_director_flag": "top réalisateur",
    "possible_franchise_flag": "franchise probable",
    "talent_score": "score talent (composite)",
}


def main() -> None:
    bundle = joblib.load(config.MODELS_DIR / "production_champion.joblib")
    pipe = bundle["pipeline"]
    feature_columns = bundle["feature_columns"]

    splits = data_mod.load_feature_regime_splits()
    X_test = splits["credits"]["X_test"].copy()
    y_test = splits["y_test"]
    cols_to_drop = [c for c in DROPPED if c in X_test.columns]
    X_test_clean = X_test.drop(columns=cols_to_drop)
    X_test_clean = X_test_clean[feature_columns]

    print(f"Test set: {X_test_clean.shape}  classes: {sorted(set(y_test))}")
    print(f"Computing permutation importance (n_repeats={N_REPEATS}, scoring=f1_macro)…")

    result = permutation_importance(
        pipe,
        X_test_clean,
        y_test,
        n_repeats=N_REPEATS,
        random_state=RANDOM_STATE,
        scoring="f1_macro",
    )

    rows = sorted(
        zip(feature_columns, result.importances_mean, result.importances_std),
        key=lambda r: r[1],
        reverse=True,
    )

    print("\n=== Permutation importance ranking ===")
    for name, mean, std in rows:
        print(f"  {name:<32s}  Δmacro-F1 = {mean:+.4f}  ± {std:.4f}")

    labels = [PRETTY.get(name, name) for name, _, _ in rows][::-1]
    means = [m for _, m, _ in rows][::-1]
    stds = [s for _, _, s in rows][::-1]

    pos_color = "#1E3A8A"
    neg_color = "#94A3B8"
    colors = [pos_color if v > 0 else neg_color for v in means]

    fig, ax = plt.subplots(figsize=(10.0, 7.2))
    bars = ax.barh(labels, means, color=colors, xerr=stds, ecolor="#CBD5E1", capsize=2.5)
    ax.axvline(0, color="#0F172A", lw=0.6)
    ax.set_xlabel("Baisse moyenne du macro-F1 quand on permute la feature")
    ax.set_title(
        "Importance des variables — champion de production (LR tunée, 25 features)\n"
        "Permutation importance · test set · scoring = macro-F1 · 30 répétitions",
        loc="left",
        fontsize=11,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3)
    max_v = max(means)
    for bar, v in zip(bars, means):
        x = v + (max_v * 0.012 if v >= 0 else -max_v * 0.012)
        ha = "left" if v >= 0 else "right"
        ax.text(x, bar.get_y() + bar.get_height() / 2, f"{v:+.3f}", va="center",
                ha=ha, fontsize=8, color="#0F172A")

    plt.tight_layout()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
