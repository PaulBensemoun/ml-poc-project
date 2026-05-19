"""Fixed Streamlit entry point for the project template."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from config import MODEL_METRICS_FILE


def build_app() -> None:
    """Render the project Streamlit application.

    Replace placeholder sections with business narrative, plots, model
    comparison, and a prediction workflow. The function name and file location
    are fixed because ``scripts/main.py`` launches Streamlit with this module.
    """

    st.set_page_config(
        page_title="Movie investment decision support (PoC)",
        layout="wide",
    )

    st.title("Movie investment decision support")
    st.write(
        "Pre-release signals → commercial success classes (ROI-based target). "
        "Customize this app after modeling and evaluation."
    )

    st.subheader("Roadmap (template)")
    st.markdown(
        """
        - Business framing: predict success *before* release using only pre-release fields.
        - Dataset audit and target engineering (ROI classes; strict leakage rules).
        - Model comparison (e.g. Random Forest, XGBoost, AdaBoost) via shared metrics.
        - Interactive demo aligned with investor-facing storytelling.
        """
    )

    st.subheader("Latest evaluation results")
    if MODEL_METRICS_FILE.exists():
        metrics_df = pd.read_csv(MODEL_METRICS_FILE)
        st.dataframe(metrics_df, use_container_width=True)
    else:
        st.info(
            "Run `python scripts/main.py` after implementing `load_dataset_split`, "
            "`compute_metrics`, and saving trained models to generate "
            "`results/model_metrics.csv`."
        )


if __name__ == "__main__":
    build_app()
