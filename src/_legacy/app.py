"""Client-facing Streamlit product: Movie Investment Intelligence."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import pandas as pd
import streamlit as st

import app_utils as au
from config import CASE_STUDIES_FILE, ERROR_ANALYSIS_FULL_FILE

APP_TITLE = "Movie Investment Intelligence"
APP_SUBTITLE = "Pre-release decision support for portfolio triage, package evaluation, and risk review."

PAGES = [
    "Movie Review Queue",
    "Package Simulator",
    "Decision Guidance",
]

GENRE_OPTIONS = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "Thriller", "War", "Western",
]

LANG_OPTIONS = ["en", "fr", "es", "de", "ja", "hi", "zh", "ko", "it", "ru"]

QUEUE_TABS = {
    "Credits rescues": "credits_rescue",
    "High-confidence failures": "high_confidence_failure",
    "Strong correct": "strong_correct",
}


def _sidebar_nav() -> str:
    st.sidebar.markdown(f"**{APP_TITLE}**")
    st.sidebar.caption(APP_SUBTITLE)
    au.render_demo_path_expander()

    if "selected_page" not in st.session_state:
        st.session_state.selected_page = PAGES[0]
    legacy_map = {
        "Case studies": "Movie Review Queue",
        "Interactive prediction": "Package Simulator",
        "Business recommendations": "Decision Guidance",
    }
    if st.session_state.selected_page in legacy_map:
        st.session_state.selected_page = legacy_map[st.session_state.selected_page]

    idx = PAGES.index(st.session_state.selected_page) if st.session_state.selected_page in PAGES else 0
    page = st.sidebar.radio("Navigate", PAGES, index=idx, label_visibility="collapsed")
    st.session_state.selected_page = page

    st.sidebar.divider()
    if au.artifacts_ready():
        st.sidebar.success("Ready")
    else:
        st.sidebar.warning("Run `python scripts/train_models.py`")
    au.render_product_sidebar_footer()
    return page


def _queue_rows_from_cases(cases: pd.DataFrame | None, err_df: pd.DataFrame, case_key: str) -> pd.DataFrame:
    if cases is not None and "case_type" in cases.columns:
        sub = cases[cases["case_type"] == case_key]
        if not sub.empty:
            return sub.head(10)
    if case_key == "credits_rescue":
        return err_df[err_df["transition"] == "wrong_to_correct"].sort_values("delta_p_true", ascending=False).head(10)
    if case_key == "high_confidence_failure":
        mask = (err_df["credits_correct"] == 0) & (err_df["confidence"] >= 0.65)
        return err_df[mask].sort_values("confidence", ascending=False).head(10)
    if case_key == "strong_correct":
        mask = (err_df["credits_correct"] == 1) & (err_df["confidence"] >= 0.65)
        return err_df[mask].sort_values("confidence", ascending=False).head(10)
    return err_df.head(0)


def _render_queue_tab(rows: pd.DataFrame, case_key: str) -> None:
    text = au.PRODUCT_QUEUE_COPY.get(case_key, "")
    if rows.empty:
        st.info("No titles in this queue with current data.")
        return
    for _, row in rows.iterrows():
        au.product_queue_card(row, text)


def _render_explore_all(err_df: pd.DataFrame) -> None:
    genres = sorted(err_df["main_genre"].dropna().unique()) if "main_genre" in err_df.columns else []
    transitions = sorted(err_df["transition"].dropna().unique()) if "transition" in err_df.columns else []
    classes = sorted(err_df["y_true"].dropna().unique()) if "y_true" in err_df.columns else []

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        genre_sel = st.multiselect("Genre", genres)
    with c2:
        trans_sel = st.multiselect("Transition", transitions)
    with c3:
        true_sel = st.multiselect("Actual class", classes)
    with c4:
        pred_sel = st.multiselect(
            "Predicted class",
            sorted(err_df["y_pred_credits"].dropna().unique()) if "y_pred_credits" in err_df.columns else [],
        )

    min_conf = st.slider("Minimum confidence", 0.0, 1.0, 0.0, 0.05) if "confidence" in err_df.columns else 0.0

    filtered = err_df.copy()
    if genre_sel:
        filtered = filtered[filtered["main_genre"].isin(genre_sel)]
    if trans_sel:
        filtered = filtered[filtered["transition"].isin(trans_sel)]
    if true_sel:
        filtered = filtered[filtered["y_true"].isin(true_sel)]
    if pred_sel:
        filtered = filtered[filtered["y_pred_credits"].isin(pred_sel)]
    if "confidence" in filtered.columns:
        filtered = filtered[filtered["confidence"] >= min_conf]

    st.caption(f"{len(filtered)} titles match · {len(err_df)} in review pool")

    if filtered.empty:
        st.info("No titles match filters.")
        return

    titles = sorted(filtered["title"].astype(str).unique())
    pick = st.selectbox("Select title", titles)
    row = filtered.loc[filtered["title"].astype(str) == pick].iloc[0]

    interp = au.transition_interpretation(str(row.get("transition", "")))
    au.movie_diagnostic_card(row)
    st.caption(interp)

    if st.button("Load profile into Package Simulator", type="primary"):
        st.session_state.simulator_prefill = au.row_to_simulator_prefill(row)
        st.session_state.selected_page = "Package Simulator"
        st.rerun()

    with st.expander("Full data table"):
        cols = [c for c in filtered.columns if c not in ("original_title", "id")]
        au.show_dataframe(au.rename_columns_readable(filtered[cols].head(100)))


def page_review_queue() -> None:
    st.title("Movie Review Queue")
    st.caption("Triage test-set titles by risk profile, model transition, and confidence.")

    err_df = au.load_csv(str(ERROR_ANALYSIS_FULL_FILE))
    if err_df is None:
        st.warning("Review data unavailable. Run `python scripts/train_models.py`.")
        return

    cases = au.load_csv(str(CASE_STUDIES_FILE))

    tab_labels = list(QUEUE_TABS.keys()) + ["Explore all"]
    tabs = st.tabs(tab_labels)
    for i, case_key in enumerate(QUEUE_TABS.values()):
        with tabs[i]:
            _render_queue_tab(_queue_rows_from_cases(cases, err_df, case_key), case_key)
    with tabs[-1]:
        _render_explore_all(err_df)


def _simulator_defaults() -> dict[str, Any]:
    bundle = au.get_champion_bundle()
    if bundle is None:
        return dict(au.SIMULATOR_PRESETS["Franchise action movie"])
    base = dict(au.SIMULATOR_PRESETS["Franchise action movie"])
    base.update({k: v for k, v in bundle["artifacts"].get("input_defaults", {}).items() if v is not None})
    return base


def _resolve_simulator_defaults(preset: str) -> dict[str, Any]:
    if preset != "Custom":
        return dict(au.SIMULATOR_PRESETS[preset])
    d = _simulator_defaults()
    prefill = st.session_state.get("simulator_prefill")
    if prefill:
        d.update({k: v for k, v in prefill.items() if v is not None})
    return d


def _int_default(d: dict, key: str, fallback: int) -> int:
    try:
        return int(float(d.get(key, fallback)))
    except (TypeError, ValueError):
        return fallback


def _director_label(name: str) -> str:
    if name == "__missing__":
        return "Unknown"
    if name == "__custom__":
        return "Custom name…"
    return name


def _director_input(d: dict[str, Any]) -> str:
    options = ["__missing__", "__custom__"] + au.get_director_names()
    current = str(d.get("director_name", "__missing__")).strip()
    if current in options and current != "__custom__":
        idx = options.index(current)
    elif current not in ("__missing__", "__other__", ""):
        idx = options.index("__custom__")
    else:
        idx = 0
    choice = st.selectbox("Director", options, index=idx, format_func=_director_label)
    if choice == "__custom__":
        custom = st.text_input("Director name", value=current if current not in options else "")
        return custom.strip() or "__missing__"
    return choice


def page_simulator() -> None:
    st.title("Package Simulator")
    st.caption("Estimate commercial profile for a hypothetical pre-release package.")

    st.info(
        "Decision-support simulator only — not an automatic greenlight engine. "
        "Use outputs to structure discussion and triage."
    )

    if not au.artifacts_ready():
        au.show_missing_artifacts_warning()
        return

    if st.session_state.get("simulator_prefill"):
        c1, c2 = st.columns([4, 1])
        with c1:
            st.success("Loaded profile from Movie Review Queue.")
        with c2:
            if st.button("Clear"):
                del st.session_state["simulator_prefill"]
                st.rerun()

    preset_options = ["Custom"] + list(au.SIMULATOR_PRESETS.keys())
    preset = st.selectbox("Package template", preset_options)
    d = _resolve_simulator_defaults(preset)

    with st.form("simulator_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            budget = st.number_input("Budget (USD)", 0, value=_int_default(d, "budget", 50_000_000), step=1_000_000)
            runtime = st.number_input("Runtime (min)", 1, value=_int_default(d, "runtime", 110))
            gi = GENRE_OPTIONS.index(d["main_genre"]) if d.get("main_genre") in GENRE_OPTIONS else 0
            main_genre = st.selectbox("Genre", GENRE_OPTIONS, index=gi)
            li = LANG_OPTIONS.index(d["original_language"]) if d.get("original_language") in LANG_OPTIONS else 0
            original_language = st.selectbox("Language", LANG_OPTIONS, index=li)
        with c2:
            release_month = st.number_input("Release month", 1, 12, _int_default(d, "release_month", 6))
            release_quarter = st.number_input("Release quarter", 1, 4, _int_default(d, "release_quarter", 2))
            genre_count = st.number_input("Genre count", 1, value=_int_default(d, "genre_count", 2))
            production_company_count = st.number_input("Prod. companies", 0, _int_default(d, "production_company_count", 2))
        with c3:
            production_country_count = st.number_input("Prod. countries", 0, _int_default(d, "production_country_count", 1))
            spoken_language_count = st.number_input("Languages", 0, _int_default(d, "spoken_language_count", 1))
            cast_size = st.number_input("Cast size", 0, _int_default(d, "cast_size", 25))
            crew_size = st.number_input("Crew size", 0, _int_default(d, "crew_size", 20))

        c4, c5, c6 = st.columns(3)
        with c4:
            writer_count = st.number_input("Writers", 0, _int_default(d, "writer_count", 3))
            known_actor_count = st.number_input("Known actors", 0, _int_default(d, "known_actor_count", 2))
            top_billed_cast_count = st.number_input("Top billed", 0, _int_default(d, "top_billed_cast_count", 4))
        with c5:
            director_name = _director_input(d)
            possible_franchise_flag = st.selectbox("Franchise", [0, 1], index=int(d.get("possible_franchise_flag", 0)))
            ensemble_cast_flag = st.selectbox("Ensemble cast", [0, 1], index=int(d.get("ensemble_cast_flag", 0)))
        with c6:
            top_director_flag = st.selectbox("Top director", [0, 1], index=int(d.get("top_director_flag", 0)))

        run = st.form_submit_button("Run estimate", type="primary")

    if not run:
        return

    user_inputs = {
        "budget": budget,
        "runtime": runtime,
        "main_genre": main_genre,
        "original_language": original_language,
        "release_month": release_month,
        "release_quarter": release_quarter,
        "genre_count": genre_count,
        "production_company_count": production_company_count,
        "production_country_count": production_country_count,
        "spoken_language_count": spoken_language_count,
        "cast_size": cast_size,
        "crew_size": crew_size,
        "writer_count": writer_count,
        "director_name": director_name,
        "known_actor_count": known_actor_count,
        "top_billed_cast_count": top_billed_cast_count,
        "possible_franchise_flag": possible_franchise_flag,
        "ensemble_cast_flag": ensemble_cast_flag,
        "top_director_flag": top_director_flag,
    }

    try:
        from inference import predict_movie_profile

        result = predict_movie_profile(user_inputs)
    except Exception as exc:
        st.error(f"Estimate failed: {exc}")
        return

    st.markdown("---")
    r1, r2, r3 = st.columns(3)
    with r1:
        au.metric_card("Outcome", str(result["prediction"]).upper())
    with r2:
        au.metric_card("Confidence", au.format_probability(result["confidence"]))
    with r3:
        au.metric_card("Risk", result["risk_level"].split("—")[0].strip()[:28])

    for label in ("flop", "average", "hit"):
        p = float(result["probabilities"].get(label, 0))
        st.write(f"**{label.capitalize()}** — {au.format_probability(p)}")
        st.progress(min(max(p, 0.0), 1.0))

    au.risk_callout(result["risk_level"])
    st.markdown(result["business_interpretation"])

    st.markdown("**Profile drivers**")
    for line in au.profile_drivers(user_inputs):
        st.markdown(f"- {line}")


def page_guidance() -> None:
    st.title("Decision Guidance")
    st.caption("How studios and investors should use this product.")

    c1, c2, c3 = st.columns(3)
    with c1:
        au.use_case_card(
            "Portfolio triage",
            "Screen projects in development. Prioritize analyst review on flagged titles.",
        )
    with c2:
        au.use_case_card(
            "Packaging evaluation",
            "Test cast, director, and scale scenarios. Discuss signal shifts — not causality.",
        )
    with c3:
        au.use_case_card(
            "Risk review queue",
            "Escalate low-confidence and high-confidence failures to human analysts.",
        )

    au.insight_box(
        "Responsible use",
        "Do not use for automatic greenlighting. Do not replace executive judgment. "
        "Do not claim that adding talent guarantees success. Always validate with market context.",
        box_type="warn",
    )


_PAGE_HANDLERS = {
    "Movie Review Queue": page_review_queue,
    "Package Simulator": page_simulator,
    "Decision Guidance": page_guidance,
}


def build_app() -> None:
    """Render the project Streamlit application."""

    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    au.inject_custom_css()

    page = _sidebar_nav()
    handler = _PAGE_HANDLERS.get(page)
    if handler:
        handler()


if __name__ == "__main__":
    build_app()
