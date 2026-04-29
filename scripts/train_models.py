"""Train baseline classifiers and save them to ``models/``."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from config import MODELS_DIR  # noqa: E402
from data import load_dataset_split  # noqa: E402


def main() -> None:
    X_train, _X_test, y_train, _y_test = load_dataset_split()

    lr = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(max_iter=500, random_state=42),
            ),
        ]
    )
    lr.fit(X_train, y_train)
    lr_path = MODELS_DIR / "logistic_regression.joblib"
    joblib.dump(lr, lr_path)
    print(f"Saved logistic regression to {lr_path}")

    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    rf_path = MODELS_DIR / "random_forest.joblib"
    joblib.dump(rf, rf_path)
    print(f"Saved random forest to {rf_path}")

    xgb = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
        eval_metric="logloss",
        use_label_encoder=False,
    )
    xgb.fit(X_train, y_train)
    xgb_path = MODELS_DIR / "xgboost.joblib"
    joblib.dump(xgb, xgb_path)
    print(f"Saved XGBoost to {xgb_path}")


if __name__ == "__main__":
    main()
