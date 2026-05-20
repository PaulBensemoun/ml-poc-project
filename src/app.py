"""CinéSignal — Movie Success Intelligence (Streamlit production app).

Entry point. Renders navigation, language toggle, brand header, and dispatches
to one of the four pages: Dashboard, Predict, Compare, Insights.
"""

from __future__ import annotations

import sys
from pathlib import Path

_src = Path(__file__).resolve().parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

import streamlit as st

import config
import ui_components as uc
from ui_styles import LANGUAGES, LOGO_SVG, get_lang, inject_css, set_lang, t


PAGE_KEYS = ["dashboard", "predict", "compare", "insights"]


def _model_ready() -> bool:
    model_path = config.MODELS["credits_logistic_regression"]["path"]
    return model_path.exists() and config.TRAIN_ARTIFACTS_FILE.exists()


def _brand_header() -> None:
    st.sidebar.markdown(
        f"""
        <div class="brand-header">
            <div class="brand-logo" style="background:transparent;padding:0;">{LOGO_SVG}</div>
            <div>
                <p class="brand-name">{t('brand_name')}</p>
                <p class="brand-tag">{t('brand_tag')}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _language_picker() -> None:
    lang_keys = list(LANGUAGES.keys())
    current = get_lang()
    idx = lang_keys.index(current) if current in lang_keys else 0
    choice = st.sidebar.radio(
        t("lang_label"),
        lang_keys,
        index=idx,
        format_func=lambda k: LANGUAGES[k],
        horizontal=True,
        key="lang_radio",
    )
    if choice != current:
        set_lang(choice)
        st.rerun()


def _navigation() -> str:
    label_map = {
        "dashboard": t("nav_dashboard"),
        "predict": t("nav_predict"),
        "compare": t("nav_compare"),
        "insights": t("nav_insights"),
    }

    target = st.session_state.pop("target_page", None)
    if target in PAGE_KEYS:
        # Force both the canonical key and the widget key so the radio reflects
        # the programmatic navigation (e.g. Dashboard "Try this case" button).
        st.session_state["selected_page"] = target
        st.session_state["nav_radio"] = target

    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "dashboard"

    current = st.session_state["selected_page"]
    if current not in PAGE_KEYS:
        current = "dashboard"

    idx = PAGE_KEYS.index(current)
    choice = st.sidebar.radio(
        t("nav_label"),
        PAGE_KEYS,
        index=idx,
        format_func=lambda k: label_map[k],
        key="nav_radio",
    )
    st.session_state["selected_page"] = choice
    return choice


def _sidebar_status() -> None:
    st.sidebar.divider()
    if _model_ready():
        st.sidebar.success("✓ " + t("sidebar_status_ready"))
    else:
        st.sidebar.warning(t("sidebar_status_missing"))

    deck_path = config.PROJECT_ROOT / "presentation" / "movie_success_technical_deck.pptx"
    if deck_path.exists():
        with deck_path.open("rb") as fh:
            st.sidebar.download_button(
                "⬇ " + t("deck_link"),
                data=fh.read(),
                file_name=deck_path.name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )

    st.sidebar.caption(t("sidebar_footer"))


def _dispatch(page: str) -> None:
    if not _model_ready() and page != "dashboard" and page != "insights":
        st.error(t("sidebar_status_missing"))
        st.code("python scripts/train_models.py", language="bash")
        return

    if page == "dashboard":
        from views import dashboard
        dashboard.render()
    elif page == "predict":
        from views import predict
        predict.render()
    elif page == "compare":
        from views import compare
        compare.render()
    elif page == "insights":
        from views import insights
        insights.render()


def build_app() -> None:
    """Streamlit app entry point (kept for `scripts/main.py` compatibility)."""

    st.set_page_config(
        page_title="CinéSignal — Movie Success Intelligence",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()

    _brand_header()
    _language_picker()
    page = _navigation()
    _sidebar_status()

    _dispatch(page)


if __name__ == "__main__":
    build_app()
