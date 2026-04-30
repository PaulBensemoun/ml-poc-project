"""Streamlit entry point for the v1 historical baseline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from config import DATA_DIR, MODEL_METRICS_FILE, MODELS


def build_app() -> None:
    """Render the project Streamlit application.

    The function name and file location are kept so ``v1/scripts/main.py`` can
    launch the historical Online Retail II baseline without changing behavior.
    """

    st.set_page_config(
        page_title="Next Best Product Recommendation Engine", layout="wide"
    )

    st.title("Next Best Product Recommendation Engine")
    st.markdown(
        """
        **Objective:** Increase basket size and conversion by guiding each customer toward
        offers that best fit their shopping patterns.

        **How it works:** The model learns from historical purchase patterns and customer
        behavior to estimate the affinity between a customer and products they have not yet
        purchased. It identifies which items are most likely to be relevant for a given
        customer based on similarities with past transactions.
        """
    )

    st.markdown("")  # breathing room

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

    st.markdown("")
    st.divider()
    _render_customer_product_insights()

    st.markdown("")
    st.divider()
    _render_next_best_product_demo()

    st.markdown("")
    st.divider()
    st.subheader("How this recommendation system can be used")
    st.markdown(
        """
        - **Homepage personalization** — Show top recommended products when the user logs in.

        - **Email campaigns** — Send personalized product suggestions based on predicted preferences.

        - **Cart upsell** — Recommend complementary or higher-value items during checkout.

        - **CRM / sales targeting** — Help marketing teams target high-value customers with tailored offers.
        """
    )


def _segmentation_by_spend(customer_feats: pd.DataFrame) -> pd.DataFrame:
    """Low (bottom 50%), Medium (50–90%), High (top 10%) — counts, avg spend, revenue share."""
    spend = customer_feats["total_spend"].astype(float)
    total_rev = spend.sum()
    q50 = float(spend.quantile(0.5))
    q90 = float(spend.quantile(0.9))

    low = spend[spend <= q50]
    med = spend[(spend > q50) & (spend <= q90)]
    high = spend[spend > q90]

    def row(label: str, s: pd.Series) -> dict[str, Any]:
        n = int(s.shape[0])
        avg = float(s.mean()) if n else 0.0
        share = float(s.sum() / total_rev * 100) if total_rev > 0 else 0.0
        return {
            "Segment": label,
            "Customers": f"{n:,}",
            "Avg spend": f"{avg:,.2f}",
            "Revenue share": f"{share:.1f}%",
        }

    return pd.DataFrame(
        [
            row("Low value (bottom 50%)", low),
            row("Medium value (50th–90th pct.)", med),
            row("High value (top 10%)", high),
        ]
    )


ScenarioKey = Literal["high", "medium", "low"]


def _pick_demo_scenario_customers(customer_feats: pd.DataFrame) -> dict[ScenarioKey, str]:
    """Pick one representative customer per spend tier (deterministic, from total_spend)."""
    cf = customer_feats[["Customer ID", "total_spend"]].copy()
    cf["Customer ID"] = cf["Customer ID"].astype(str)
    spend = cf["total_spend"].astype(float)
    q30 = float(spend.quantile(0.30))
    q50 = float(spend.quantile(0.50))
    q70 = float(spend.quantile(0.70))
    q90 = float(spend.quantile(0.90))

    low_pool = cf[spend <= q30]
    med_pool = cf[(spend >= q50) & (spend <= q70)]
    high_pool = cf[spend >= q90]

    def pick_closest_to_median(pool: pd.DataFrame) -> str:
        if pool.empty:
            return ""
        med = float(pool["total_spend"].median())
        idx = (pool["total_spend"] - med).abs().idxmin()
        return str(pool.loc[idx, "Customer ID"])

    low_id = pick_closest_to_median(low_pool)
    med_id = pick_closest_to_median(med_pool)
    high_id = pick_closest_to_median(high_pool)

    if not med_id:
        q45, q75 = float(spend.quantile(0.45)), float(spend.quantile(0.75))
        med_id = pick_closest_to_median(cf[(spend >= q45) & (spend <= q75)])
    if not high_id:
        high_id = pick_closest_to_median(cf[spend >= float(spend.quantile(0.85))])
    if not low_id:
        low_id = pick_closest_to_median(cf[spend <= float(spend.quantile(0.35))])

    def by_quantile(q: float) -> str:
        target = float(spend.quantile(q))
        idx = (spend - target).abs().idxmin()
        return str(cf.loc[idx, "Customer ID"])

    if not low_id:
        low_id = by_quantile(0.15)
    if not med_id:
        med_id = by_quantile(0.60)
    if not high_id:
        high_id = by_quantile(0.95)

    return {"high": high_id, "medium": med_id, "low": low_id}


def _render_customer_product_insights() -> None:
    st.subheader("Customer & Product Insights")

    customer_feats, product_feats, _purchased, descr, _, _, _ = _reload_clean_dataset_for_demo()

    st.markdown(
        """
        **Product catalogue** — Line frequency reveals hero SKUs. **Spend mix** — Segmentation
        below shows where customers and revenue concentrate (stable under heavy-tailed spend).
        """
    )
    st.markdown("")

    st.markdown("**A · Top catalogue items (invoice lines)**")
    top_products = product_feats.nlargest(10, "product_popularity").copy()
    top_products["Description"] = top_products["StockCode"].map(descr)
    top_products = top_products.rename(
        columns={"product_popularity": "Popularity (line appearances)"}
    ).loc[:, ["Description", "Popularity (line appearances)"]]
    st.dataframe(top_products, use_container_width=True, hide_index=True)

    st.markdown("")
    st.markdown("**B · Customer value segments (total spend)**")
    seg_tbl = _segmentation_by_spend(customer_feats)
    st.dataframe(seg_tbl, use_container_width=True, hide_index=True)
    st.caption(
        "Segments use spend quantiles on the cleaned base — revenue share sums to ~100%."
    )


@st.cache_data(show_spinner="Loading recommendation data…")
def _reload_clean_dataset_for_demo() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    dict[str, set[str]],
    pd.Series,
    pd.Series,
    pd.DataFrame,
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

    spend_q90 = float(customer_feats["total_spend"].quantile(0.9))
    hv_ids = set(
        customer_feats.loc[
            customer_feats["total_spend"].astype(float) >= spend_q90, "Customer ID"
        ].astype(str)
    )
    df_hv = df["Customer ID"].isin(hv_ids)
    hv_line_counts = df.loc[df_hv].groupby("StockCode").size()
    total_line_counts = df.groupby("StockCode").size()
    product_hv_line_share = (hv_line_counts / total_line_counts).fillna(0.0)

    inv_skus = df[["Invoice", "StockCode"]].copy()
    inv_to_skus_map = inv_skus.groupby("Invoice")["StockCode"].apply(
        lambda s: frozenset(s.astype(str).unique())
    )

    purchased = df[["Customer ID", "StockCode"]].drop_duplicates()
    purchased_by_customer: dict[str, set[str]] = (
        purchased.groupby("Customer ID")["StockCode"].apply(set).to_dict()
    )
    descr = df.groupby("StockCode")["Description"].first()
    return (
        customer_feats,
        product_feats,
        purchased_by_customer,
        descr,
        product_hv_line_share,
        inv_skus,
        inv_to_skus_map,
    )


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
        return joblib.load(path), None
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


def _co_purchase_invoice_counts(
    stock_codes: list[str],
    bought: set[str],
    inv_skus: pd.DataFrame,
    inv_to_skus_map: pd.Series,
) -> dict[str, int]:
    """Count invoices where the product appears alongside any SKU the customer already bought."""
    if not bought:
        return {sc: 0 for sc in stock_codes}
    out: dict[str, int] = {}
    for sc in stock_codes:
        invs = inv_skus.loc[inv_skus["StockCode"].astype(str) == sc, "Invoice"].unique()
        c = 0
        for inv in invs:
            skus = inv_to_skus_map.get(inv, frozenset())
            if skus & bought:
                c += 1
        out[sc] = c
    return out


def _compact_reasons_for_row(
    stock_code: str,
    product_feats: pd.DataFrame,
    cust_spend: float,
    cust_avg_basket: float,
    pop_q75: float,
    price_q75: float,
    spend_q90: float,
    hv_line_share: float,
    co_purchase_invoices: int,
    max_co_in_batch: int,
) -> str:
    """Up to two short, heuristic explanations (deterministic, business-oriented)."""
    pf = product_feats.set_index(product_feats["StockCode"].astype(str))
    if stock_code not in pf.index:
        return "Aligned with this customer's history and segment"
    pr = pf.loc[stock_code]
    pop = float(pr["product_popularity"])
    price = float(pr["average_price"])
    reasons: list[str] = []

    strong_co = co_purchase_invoices >= 3 or (
        co_purchase_invoices > 0 and co_purchase_invoices == max_co_in_batch
    )
    if strong_co:
        reasons.append(
            "Often bought together with products this customer already purchased"
        )
    if len(reasons) < 2 and hv_line_share >= 0.30:
        reasons.append("Frequently purchased by similar high-value customers")
    if len(reasons) < 2 and pop >= pop_q75:
        reasons.append("Popular product across the catalogue")
    if len(reasons) < 2 and cust_avg_basket > 0:
        low, high = 0.4 * cust_avg_basket, 2.5 * cust_avg_basket
        if low <= price <= high:
            reasons.append("Matches customer's typical basket size")
    if len(reasons) < 2 and cust_spend >= spend_q90 and price >= price_q75:
        reasons.append("High-value item aligned with this customer profile")
    if not reasons:
        reasons.append("Aligned with this customer's history and segment")
    return "; ".join(reasons[:2])


def _render_next_best_product_demo() -> None:
    st.subheader("Interactive recommendation")

    (
        customer_feats,
        product_feats,
        purchased_by_customer,
        descr,
        product_hv_line_share,
        inv_skus,
        inv_to_skus_map,
    ) = _reload_clean_dataset_for_demo()

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

    if customer_feats.empty:
        st.info("No customers found in dataset.")
        return

    scenario_customers = _pick_demo_scenario_customers(customer_feats)
    scenario_options: list[tuple[str, ScenarioKey]] = [
        ("High-value customer", "high"),
        ("Medium-value customer", "medium"),
        ("Low-value customer", "low"),
    ]
    scenario_label_to_key = dict(scenario_options)

    st.markdown("###### Customer scenario")
    picked_label = st.radio(
        "Select customer scenario",
        options=[label for label, _ in scenario_options],
        horizontal=True,
    )
    scenario_key = scenario_label_to_key[picked_label]
    chosen = scenario_customers[scenario_key]
    st.caption(
        f"Representative **{picked_label.lower()}** for this demo — ID `{chosen}` "
        "(selected from spend tiers on the full customer base)."
    )

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
        st.markdown("")

    st.markdown("###### Recommendation scenario")
    segment_objectives: dict[ScenarioKey, str] = {
        "high": (
            "For **high-value** shoppers the emphasis is **cross-sell** and **premium** "
            "items. The objective is to maximise basket value through premium and "
            "high-affinity cross-sell opportunities."
        ),
        "medium": (
            "For **mid-value** shoppers the emphasis is **basket size** and **discovery**. "
            "The objective is to increase basket size by suggesting relevant and "
            "complementary products."
        ),
        "low": (
            "For **low-value** shoppers the emphasis is **engagement** and **conversion** "
            "(bringing them back). The objective is to re-engage this customer with "
            "accessible and popular products to increase purchase frequency."
        ),
    }
    st.markdown(
        f"""
For **customer `{chosen}`**, we emulate a plausible **online shop visit**: scoring focuses on SKU–customer pairs **not purchased before** by this shopper,
so rankings reflect a realistic **browse or replenishment journey**.

{segment_objectives[scenario_key]}
        """
    )
    if scenario_key == "high":
        st.success(
            "**High-value customer** — spend in the top ~10% of shoppers"
        )
    elif scenario_key == "medium":
        st.info(
            "**Mid-value customer** — typical shopper with moderate spend and frequency"
        )
    else:
        st.warning(
            "**Low-value customer** — occasional shopper with low total spend"
        )

    st.markdown("")
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

    cust_spend = float(
        customer_feats.loc[
            customer_feats["Customer ID"].astype(str) == chosen, "total_spend"
        ].iloc[0]
    )
    pop_q75 = float(product_feats["product_popularity"].quantile(0.75))
    price_q75 = float(product_feats["average_price"].quantile(0.75))
    spend_q90 = float(customer_feats["total_spend"].quantile(0.90))

    cfg = MODELS[model_key]

    st.markdown("")
    st.divider()
    st.subheader("Top Recommended Products")
    st.markdown("###### Top products ranked by recommendation score (relative ranking signal)")
    st.caption(
        f"Model: **{cfg['name']}** (best F1 among Logistic Regression vs XGBoost on held-out metrics)."
    )
    st.caption(
        "Scores represent relative likelihood based on historical patterns, not actual "
        "conversion probabilities."
    )
    st.markdown("")
    hc0, hc1, hc2, hc3, hc4 = st.columns([0.45, 1.0, 2.8, 1.0, 3.2])
    with hc0:
        st.caption("Rank")
    with hc1:
        st.caption("SKU")
    with hc2:
        st.caption("Description")
    with hc3:
        st.caption("Score")
    with hc4:
        st.caption("Relative strength")

    for ix, (_, row) in enumerate(cand_df.reset_index(drop=True).iterrows(), start=1):
        p = float(row["proba"])
        sk = str(row["StockCode"])
        ds = str(row.get("Description", "") or "").strip() or "—"
        c0, c1, c2, c3, c4 = st.columns([0.45, 1.0, 2.8, 1.0, 3.2])
        with c0:
            st.markdown(f"**#{ix}**")
        with c1:
            st.caption(sk)
        with c2:
            st.caption(ds[:120] + ("…" if len(ds) > 120 else ""))
        with c3:
            st.markdown(f"**{p * 100:.1f}%**")
        with c4:
            st.progress(min(max(p, 0.0), 1.0))

    avg_top5 = float(cand_df["proba"].mean())
    pct = avg_top5 * 100

    st.markdown("")
    st.divider()
    st.subheader("Business impact (simulation)")
    ic1, ic2 = st.columns([1.4, 1.6])
    with ic1:
        st.metric("Avg recommendation score (top 5)", f"{pct:.1f}%")
    with ic2:
        st.markdown(
            f"*Mean **relative purchase likelihood** for the top five offers is **{pct:.1f}%** "
            "on the model’s ranking scale (not a calibrated purchase probability).*"
        )
        st.caption(
            "Scores represent relative likelihood based on historical patterns, not actual "
            "conversion probabilities."
        )
    st.caption(
        "This is a simplified proxy to discuss potential uplift from personalised "
        "recommendations—not a forecast of real-world conversion."
    )

    top_skus = cand_df["StockCode"].astype(str).tolist()
    co_counts = _co_purchase_invoice_counts(
        top_skus, bought, inv_skus, inv_to_skus_map
    )
    max_co = max(co_counts.values(), default=0)
    cust_avg_basket = (
        float(pf_row.iloc[0]["avg_basket_value"]) if not pf_row.empty else 0.0
    )

    reasons_rows = [
        {
            "Product": f"{sk} · {(str(descr.get(sk, '')) or '—')[:60]}",
            "Reason": _compact_reasons_for_row(
                sk,
                product_feats,
                cust_spend,
                cust_avg_basket,
                pop_q75,
                price_q75,
                spend_q90,
                float(product_hv_line_share.get(sk, 0.0)),
                co_counts.get(sk, 0),
                max_co,
            ),
        }
        for sk in top_skus
    ]
    reasons_df = pd.DataFrame(reasons_rows)

    st.markdown("")
    st.divider()
    st.subheader("Why these picks?")
    st.dataframe(reasons_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    build_app()
