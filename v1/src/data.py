"""Dataset loading contract for the v1 historical baseline.

``load_dataset_split`` lets ``v1/scripts/main.py`` evaluate every configured
model on the same test split.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from config import DATA_DIR


def load_dataset_split() -> tuple[Any, Any, Any, Any]:
    """Return the dataset split used for model evaluation.

    Expected return value:
        A tuple ``(X_train, X_test, y_train, y_test)``.

    Constraints:
    - ``X_train`` and ``X_test`` must contain feature data in a format accepted
      by the trained models stored in ``config.MODELS``.
    - ``y_train`` and ``y_test`` must contain the corresponding targets.
    - ``y_test`` must align with the predictions produced by each loaded model.

    Typical choices for the return types are ``pandas.DataFrame`` /
    ``pandas.Series`` or ``numpy.ndarray``.
    """

    df = pd.read_csv(DATA_DIR / "online_retail_II.csv")

    df = df.dropna(subset=["Customer ID", "StockCode", "Description"])
    df = df[(df["Quantity"] > 0) & (df["Price"] > 0)].copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df["Customer ID"] = df["Customer ID"].astype(str)

    df["line_total"] = df["Quantity"] * df["Price"]
    customer_feats = df.groupby("Customer ID", as_index=False).agg(
        total_spend=("line_total", "sum"),
        total_quantity=("Quantity", "sum"),
        number_of_transactions=("Invoice", "nunique"),
    )
    # Average order value per distinct invoice (basket) for this customer.
    customer_feats["avg_basket_value"] = customer_feats["total_spend"] / customer_feats[
        "number_of_transactions"
    ].replace(0, np.nan)
    customer_feats["avg_basket_value"] = customer_feats["avg_basket_value"].fillna(0)

    product_feats = df.groupby("StockCode", as_index=False).agg(
        product_popularity=("Invoice", "count"),
        average_price=("Price", "mean"),
    )

    # Positive examples = observed purchases: each distinct (customer, product)
    # pair that appears in the cleaned transaction log gets label 1.
    positive_pairs = df[["Customer ID", "StockCode"]].drop_duplicates()
    n_pos = len(positive_pairs)

    positives = positive_pairs.assign(target=1)
    positives = positives.merge(customer_feats, on="Customer ID", how="left")
    positives = positives.merge(product_feats, on="StockCode", how="left")

    # Negative examples = sampled unobserved customer-product pairs (label 0).
    # This is a simplified POC formulation: we balance the dataset by drawing
    # random pairs and excluding anything that is already a positive purchase.
    cust_uniques = np.asarray(df["Customer ID"].unique())
    prod_uniques = np.asarray(df["StockCode"].unique())
    rng = np.random.RandomState(42)

    batch = max(10 * n_pos, 10_000)
    ci = rng.randint(0, len(cust_uniques), size=batch)
    pi = rng.randint(0, len(prod_uniques), size=batch)
    candidates = pd.DataFrame(
        {"Customer ID": cust_uniques[ci], "StockCode": prod_uniques[pi]}
    )
    candidates = candidates.drop_duplicates()
    negatives_raw = candidates.merge(
        positive_pairs,
        on=["Customer ID", "StockCode"],
        how="left",
        indicator=True,
    )
    negatives_raw = negatives_raw[negatives_raw["_merge"] == "left_only"][
        ["Customer ID", "StockCode"]
    ]

    if len(negatives_raw) < n_pos:
        extra = max(batch * 2, 20 * n_pos)
        ci2 = rng.randint(0, len(cust_uniques), size=extra)
        pi2 = rng.randint(0, len(prod_uniques), size=extra)
        more = pd.DataFrame(
            {"Customer ID": cust_uniques[ci2], "StockCode": prod_uniques[pi2]}
        )
        negatives_raw = (
            pd.concat([negatives_raw, more], ignore_index=True)
            .drop_duplicates()
            .merge(positive_pairs, on=["Customer ID", "StockCode"], how="left", indicator=True)
        )
        negatives_raw = negatives_raw[negatives_raw["_merge"] == "left_only"][
            ["Customer ID", "StockCode"]
        ]

    if len(negatives_raw) < n_pos:
        raise RuntimeError(
            "Could not draw enough negative (Customer ID, StockCode) pairs in batch."
        )

    negative_pairs = negatives_raw.sample(n=n_pos, random_state=42)

    negatives = negative_pairs.assign(target=0)
    negatives = negatives.merge(customer_feats, on="Customer ID", how="left")
    negatives = negatives.merge(product_feats, on="StockCode", how="left")

    combined = pd.concat([positives, negatives], ignore_index=True)
    combined = combined.sample(frac=1.0, random_state=42).reset_index(drop=True)

    y = combined["target"]
    X = combined.drop(columns=["Customer ID", "StockCode", "target"])
    X = X.select_dtypes(include=[np.number])
    X = X.fillna(0)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    return (X_train, X_test, y_train, y_test)
