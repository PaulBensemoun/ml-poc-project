"""Fixed Streamlit entry point for the project template."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from config import DATA_DIR, MODEL_METRICS_FILE, MODELS
from data import load_dataset_split
from model_io import load_model


def build_app() -> None:
    """Render the project Streamlit application.

    Students should replace the placeholder sections with their own visualizations,
    explanations, and prediction workflow. The function name and file location are
    fixed because ``scripts/main.py`` launches Streamlit with this module.
    """

    st.set_page_config(
        page_title="Next Best Product Recommendation Engine", layout="wide"
    )

    st.title("Next Best Product Recommendation Engine")
    st.markdown(
        """
        **Objective:** Increase basket size and conversion by guiding each customer toward
        the offer they are most likely to buy next.

        **How it works:** A trained classifier assigns a purchase probability for each
        customer–product pair; we prioritize products with the strongest predicted uplift.
        """
    )

    st.divider()
    st.subheader("Model performance")
    if MODEL_METRICS_FILE.exists():
        metrics_df = pd.read_csv(MODEL_METRICS_FILE)
        st.dataframe(metrics_df, use_container_width=True)
    else:
        st.info(
            "Run `python scripts/main.py` after training your models to generate "
            "`results/model_metrics.csv`."
        )

    st.divider()
    _render_next_best_product_demo()


@st.cache_data(show_spinner="Loading recommendation data…")
def _reload_clean_dataset_for_demo() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[str, set[str]],
    pd.Series,
]:
    """Rebuild customer/product aggregates using the same rules as ``load_dataset_split``."""
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
    customer_feats["avg_basket_value"] = customer_feats["total_spend"] / customer_feats[
        "number_of_transactions"
    ].replace(0, np.nan)
    customer_feats["avg_basket_value"] = customer_feats["avg_basket_value"].fillna(0)

    product_feats = df.groupby("StockCode", as_index=False).agg(
        product_popularity=("Invoice", "count"),
        average_price=("Price", "mean"),
    )

    purchased = df[["Customer ID", "StockCode"]].drop_duplicates()
    purchased_by_customer: dict[str, set[str]] = (
        purchased.groupby("Customer ID")["StockCode"].apply(set).to_dict()
    )
    descr = df.groupby("StockCode")["Description"].first()
    return customer_feats, product_feats, purchased_by_customer, descr


def _pick_best_classifier_key() -> str:
    candidates = {"logistic_regression", "xgboost"}
    if MODEL_METRICS_FILE.exists():
        mdf = pd.read_csv(MODEL_METRICS_FILE)
        sub = mdf[mdf["model_key"].isin(candidates)].copy()
        if len(sub):
            best = sub.sort_values("f1", ascending=False).iloc[0]
            return str(best["model_key"])
    return "xgboost"


@st.cache_resource(show_spinner="Loading classifier…")
def _load_classifier_model(model_key: str) -> tuple[Any | None, str | None]:
    cfg = MODELS.get(model_key)
    if cfg is None:
        return None, f"Unknown model key: {model_key}"
    path = Path(cfg["path"])
    if not path.exists():
        return None, f"Missing model file: {path}"
    try:
        return load_model(path), None
    except Exception as exc:  # pragma: no cover - defensive for Streamlit UX
        return None, str(exc)


def _feature_matrix_for_candidates(
    customer_id: str,
    stock_codes: list[str],
    customer_feats: pd.DataFrame,
    product_feats: pd.DataFrame,
) -> pd.DataFrame:
    cf = customer_feats[customer_feats["Customer ID"] == customer_id]
    if cf.empty:
        return pd.DataFrame()
    cf = cf.iloc[0]
    rows: list[dict[str, Any]] = []
    pf_indexed = product_feats.set_index("StockCode")
    for sc in stock_codes:
        if sc not in pf_indexed.index:
            continue
        pr = pf_indexed.loc[sc]
        rows.append(
            {
                "total_spend": cf["total_spend"],
                "total_quantity": cf["total_quantity"],
                "number_of_transactions": cf["number_of_transactions"],
                "avg_basket_value": cf["avg_basket_value"],
                "product_popularity": pr["product_popularity"],
                "average_price": pr["average_price"],
            }
        )
    return pd.DataFrame(rows)


def _render_next_best_product_demo() -> None:
    st.subheader("Interactive recommendation")

    _split_ok = False
    try:
        load_dataset_split()
        _split_ok = True
    except Exception:
        pass
    if not _split_ok:
        st.warning("Could not load the dataset split. Check `data.load_dataset_split()` and raw data.")

    customer_feats, product_feats, purchased_by_customer, descr = _reload_clean_dataset_for_demo()

    model_key = _pick_best_classifier_key()
    model, load_err = _load_classifier_model(model_key)
    if load_err:
        st.error(load_err)
        return

    if model is None:
        st.warning("Classifier could not be loaded.")
        return

    feat_names = None
    if hasattr(model, "feature_names_in_"):
        feat_names = list(model.feature_names_in_)
    else:
        feat_names = [
            "total_spend",
            "total_quantity",
            "number_of_transactions",
            "avg_basket_value",
            "product_popularity",
            "average_price",
        ]

    cust_ids = sorted(customer_feats["Customer ID"].astype(str).unique())
    if not cust_ids:
        st.info("No customers found in dataset.")
        return

    st.markdown("###### Customer selection")
    chosen = st.selectbox("Select a Customer", options=cust_ids, index=0)

    pf_row = customer_feats[customer_feats["Customer ID"].astype(str) == chosen]
    if not pf_row.empty:
        r = pf_row.iloc[0]
        st.markdown("**Customer snapshot**")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total spend", f"{float(r['total_spend']):,.2f}")
        with m2:
            st.metric("Total quantity", f"{float(r['total_quantity']):,.0f}")
        with m3:
            st.metric("Number of transactions", f"{float(r['number_of_transactions']):,.0f}")
        with m4:
            st.metric("Avg basket value", f"{float(r['avg_basket_value']):,.2f}")
        st.divider()

    catalog = product_feats["StockCode"].astype(str).unique().tolist()
    bought = purchased_by_customer.get(chosen, set())
    unseen = [c for c in catalog if c not in bought]

    if not unseen:
        st.info("This customer already appears to have interacted with every product in the catalog slice.")
        return

    rng_seed = hash(chosen) % (2**31)
    rng = np.random.RandomState(rng_seed)
    max_score = min(1200, len(unseen))
    if len(unseen) > max_score:
        unseen = list(rng.choice(unseen, size=max_score, replace=False))

    X_df = _feature_matrix_for_candidates(
        chosen, unseen, customer_feats, product_feats
    )
    if X_df.empty or len(X_df) != len(unseen):
        st.warning("Could not align candidate products with features.")
        return

    X_df = X_df.reindex(columns=feat_names, fill_value=0)

    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_df)[:, 1]
    else:
        proba = model.predict(X_df)

    cand_df = pd.DataFrame({"StockCode": unseen, "proba": proba.astype(float)})
    cand_df = cand_df.sort_values("proba", ascending=False).head(5)
    cand_df["Description"] = cand_df["StockCode"].map(lambda s: descr.get(s, ""))

    cfg = MODELS[model_key]
    st.divider()
    st.subheader("Top Recommended Products")
    st.caption("Products ranked by predicted probability of purchase.")
    st.caption(
        f"Ranked using **{cfg['name']}** (Logistic Regression vs XGBoost: best F1 on held-out metrics)."
    )

    out = cand_df.rename(
        columns={"StockCode": "Product (Stock Code)", "proba": "Predicted probability"}
    )
    out["Predicted probability"] = out["Predicted probability"].map(
        lambda x: f"{float(x) * 100:.1f}%"
    )
    st.dataframe(
        out[["Product (Stock Code)", "Description", "Predicted probability"]],
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    build_app()
