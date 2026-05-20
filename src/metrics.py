"""Metrics contract for model comparison (classification-oriented project)."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, f1_score


def compute_metrics(y_true: Any, y_pred: Any) -> dict[str, float]:
    """Return comparable metrics for ``results/model_metrics.csv``."""

    labels = ["flop", "average", "hit"]
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)

    acc = float(accuracy_score(yt, yp))
    macro_f1 = float(f1_score(yt, yp, average="macro", labels=labels, zero_division=0))
    weighted_f1 = float(f1_score(yt, yp, average="weighted", labels=labels, zero_division=0))

    per = f1_score(yt, yp, average=None, labels=labels, zero_division=0)
    # Order matches ``labels``
    f1_flop, f1_average, f1_hit = (float(x) for x in per)

    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "f1_flop": f1_flop,
        "f1_average": f1_average,
        "f1_hit": f1_hit,
    }
