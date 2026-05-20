"""Dashboard / landing page — hero, KPIs, demo cases, onboarding."""

from __future__ import annotations

import copy
import json

import streamlit as st

import config
import form_helpers as fh
import ui_components as uc
from ui_styles import t


def _load_kpis() -> dict:
    if not config.APP_KPIS_FILE.exists():
        return {}
    with config.APP_KPIS_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def _format_pct(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def _format_int(value: float | None) -> str:
    if value is None:
        return "—"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "—"


DEMO_CASES = [
    {
        "key": "preset_franchise_action",
        "emoji": "🚀",
        "title_key": "demo_blockbuster_title",
        "desc_key": "demo_blockbuster_desc",
        "tags_keys": ["preset_franchise_action"],
        "extra_tags": ["Action", "$150M", "Summer", "Franchise"],
    },
    {
        "key": "preset_indie_drama",
        "emoji": "🎭",
        "title_key": "demo_indie_title",
        "desc_key": "demo_indie_desc",
        "tags_keys": ["preset_indie_drama"],
        "extra_tags": ["Drama", "$8M", "Fall", "Indie"],
    },
    {
        "key": "preset_low_budget_horror",
        "emoji": "👻",
        "title_key": "demo_horror_title",
        "desc_key": "demo_horror_desc",
        "tags_keys": ["preset_low_budget_horror"],
        "extra_tags": ["Horror", "$5M", "Halloween", "High ROI"],
    },
]


def _send_to_predict(preset_key: str) -> None:
    """Pre-fill the predict wizard with a preset and navigate there."""
    base = fh.empty_defaults()
    base.update(fh.model_input_defaults())
    if preset_key in fh.PRESETS:
        base.update(fh.PRESETS[preset_key])
    st.session_state["predict_inputs"] = copy.deepcopy(base)
    st.session_state["predict_preset"] = preset_key
    # Keep the selectbox-widget key in sync so the Predict page selectbox
    # reflects the demo case immediately.
    st.session_state["predict_preset_selector"] = preset_key
    st.session_state["predict_step"] = 0
    st.session_state.pop("predict_result", None)
    st.session_state.pop("predict_last_inputs", None)
    # Wipe stale wizard widget state and bump the form nonce so the widgets
    # rebuild from the new preset values on the next render.
    for key in list(st.session_state.keys()):
        if key.startswith("p1_") or key.startswith("p2_") or key.startswith("p3_"):
            del st.session_state[key]
    st.session_state["predict_form_nonce"] = int(st.session_state.get("predict_form_nonce", 0)) + 1
    st.session_state["target_page"] = "predict"
    st.session_state["_auto_run_predict"] = True
    st.rerun()


def render() -> None:
    kpis = _load_kpis()

    # Hero with stat strip baked in
    uc.hero(
        title=t("hero_title"),
        body=t("hero_body"),
        stats=[
            (_format_int(kpis.get("n_movies_total")), t("kpi_movies")),
            (_format_pct(kpis.get("champion_macro_f1")), t("kpi_macro_f1")),
            (_format_pct(kpis.get("champion_accuracy")), t("kpi_accuracy")),
        ],
    )

    # Onboarding banner (dismissable)
    if not st.session_state.get("_onboarding_dismissed", False):
        cb1, cb2 = st.columns([6, 1])
        with cb1:
            uc.onboarding_banner(t("onboarding_title"), t("onboarding_body"))
        with cb2:
            st.write("")
            if st.button(t("common_dismiss"), key="dismiss_onboarding", use_container_width=True):
                st.session_state["_onboarding_dismissed"] = True
                st.rerun()

    # Primary CTAs row
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("▶ " + t("hero_cta"), type="primary", use_container_width=True):
            st.session_state["target_page"] = "predict"
            st.rerun()
    with c2:
        if st.button("📊 " + t("insights_title"), use_container_width=True):
            st.session_state["target_page"] = "insights"
            st.rerun()

    # Demo cases — instant pre-fill + predict
    uc.section_title(t("demo_section_title"))
    st.caption(t("demo_section_subtitle"))
    demo_cols = st.columns(len(DEMO_CASES))
    for col, case in zip(demo_cols, DEMO_CASES):
        with col:
            uc.demo_card(
                emoji=case["emoji"],
                title=t(case["title_key"]),
                description=t(case["desc_key"]),
                tags=case["extra_tags"],
            )
            if st.button(
                "→ " + t("demo_try"),
                key=f"demo_btn_{case['key']}",
                use_container_width=True,
            ):
                _send_to_predict(case["key"])

    # Model KPIs
    uc.section_title(t("dashboard_kpi_title"))
    cols = st.columns(3)
    with cols[0]:
        uc.kpi_card(
            t("kpi_movies"),
            _format_int(kpis.get("n_movies_total")),
            sub=f"{t('kpi_test')}: {_format_int(kpis.get('n_test'))}",
            variant="accent",
        )
    with cols[1]:
        uc.kpi_card(
            t("kpi_accuracy"),
            _format_pct(kpis.get("champion_accuracy")),
            sub=f"{t('kpi_macro_f1')}: {_format_pct(kpis.get('champion_macro_f1'))}",
            variant="success",
        )
    with cols[2]:
        uc.kpi_card(
            t("kpi_f1_hit"),
            _format_pct(kpis.get("f1_hit")),
            sub=f"{t('kpi_f1_flop')}: {_format_pct(kpis.get('f1_flop'))}",
            variant="accent",
        )

    # Use cases
    uc.section_title(t("dashboard_value_title"))
    cols = st.columns(3)
    with cols[0]:
        uc.kpi_card(t("use_case_portfolio_title"), "01", sub=t("use_case_portfolio_body"), variant="accent")
    with cols[1]:
        uc.kpi_card(t("use_case_packaging_title"), "02", sub=t("use_case_packaging_body"), variant="accent")
    with cols[2]:
        uc.kpi_card(t("use_case_risk_title"), "03", sub=t("use_case_risk_body"), variant="accent")

    st.markdown("")
    uc.insight_box(
        t("dashboard_disclaimer_title"),
        t("dashboard_disclaimer_body"),
        kind="warn",
    )
