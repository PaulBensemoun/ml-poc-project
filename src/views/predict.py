"""Predict page — 3-step wizard with rich results, sensitivity and comparables."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import streamlit as st

import config
import form_helpers as fh
import ui_components as uc
from ui_styles import t


STATE_STEP = "predict_step"
STATE_INPUTS = "predict_inputs"
STATE_RESULT = "predict_result"
STATE_NAME = "predict_project_name"
STATE_PRESET = "predict_preset"
STATE_LAST_RUN_INPUTS = "predict_last_inputs"


def _init_state() -> None:
    if STATE_STEP not in st.session_state:
        st.session_state[STATE_STEP] = 0
    if STATE_INPUTS not in st.session_state:
        base = fh.empty_defaults()
        base.update(fh.model_input_defaults())
        st.session_state[STATE_INPUTS] = base
    if STATE_NAME not in st.session_state:
        st.session_state[STATE_NAME] = ""
    if STATE_PRESET not in st.session_state:
        st.session_state[STATE_PRESET] = "preset_custom"


STATE_FORM_NONCE = "predict_form_nonce"


def _bump_form_nonce() -> None:
    """Increment a nonce that's appended to every wizard widget key.

    Changing the key forces Streamlit to treat the widgets as brand-new ones,
    so they re-initialize from their `value=` argument instead of restoring
    any retained widget state. This is the bullet-proof way to make a
    preset change (or reset) actually refresh the form fields.
    """
    st.session_state[STATE_FORM_NONCE] = int(st.session_state.get(STATE_FORM_NONCE, 0)) + 1


def _clear_wizard_widget_keys() -> None:
    """Remove all current wizard widget keys from session_state."""
    for key in list(st.session_state.keys()):
        if key.startswith("p1_") or key.startswith("p2_") or key.startswith("p3_"):
            del st.session_state[key]


def _reset_form() -> None:
    base = fh.empty_defaults()
    base.update(fh.model_input_defaults())
    st.session_state[STATE_INPUTS] = base
    st.session_state[STATE_STEP] = 0
    st.session_state[STATE_NAME] = ""
    st.session_state[STATE_PRESET] = "preset_custom"
    st.session_state.pop(STATE_RESULT, None)
    st.session_state.pop(STATE_LAST_RUN_INPUTS, None)
    _clear_wizard_widget_keys()
    _bump_form_nonce()


def _apply_preset(preset_key: str) -> None:
    """Switch the wizard to a preset profile.

    Called from the selectbox `on_change` so the mutation lands BEFORE the
    automatic rerun. Also stales the result so the user understands the
    previous prediction no longer reflects the form.
    """
    if preset_key == "preset_custom":
        # Custom = keep current values, but do not wipe state.
        st.session_state[STATE_PRESET] = "preset_custom"
        return
    if preset_key in fh.PRESETS:
        base = fh.empty_defaults()
        base.update(fh.model_input_defaults())
        base.update(fh.PRESETS[preset_key])
        st.session_state[STATE_INPUTS] = base
        st.session_state[STATE_PRESET] = preset_key
        # Drop stale prediction so user knows it must be re-run
        st.session_state.pop(STATE_RESULT, None)
        st.session_state.pop(STATE_LAST_RUN_INPUTS, None)
        _clear_wizard_widget_keys()
        _bump_form_nonce()


def _on_preset_changed() -> None:
    """Selectbox on_change callback: apply the selected preset immediately."""
    new_choice = st.session_state.get("predict_preset_selector")
    if new_choice and new_choice != st.session_state.get(STATE_PRESET):
        _apply_preset(new_choice)


def _risk_to_i18n(risk_text: str) -> str:
    if "Low confidence" in risk_text:
        return t("risk_low")
    if "Higher confidence" in risk_text:
        return t("risk_high")
    return t("risk_medium")


def _outcome_i18n(outcome: str) -> str:
    return {
        "hit": t("outcome_hit"),
        "average": t("outcome_average"),
        "flop": t("outcome_flop"),
    }.get(outcome, outcome.upper())


def _business_i18n(outcome: str, confidence: float) -> str:
    key = {"hit": "biz_hit", "average": "biz_average", "flop": "biz_flop"}.get(outcome, "biz_average")
    return t(key, conf=f"{confidence * 100:.0f}%")


def _step_header() -> None:
    """Clickable step indicator — visual pill for the active step + buttons for the others."""
    labels = [t("step_1"), t("step_2"), t("step_3")]
    active = st.session_state[STATE_STEP]
    cols = st.columns(3, gap="small")
    for i, (col, label) in enumerate(zip(cols, labels)):
        with col:
            if i == active:
                # Active step: a styled pill, not a disabled button (avoids ghost-text issue)
                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #2046C9, #2C5BFF);
                        color: white;
                        padding: 0.55rem 0.9rem;
                        border-radius: 0.5rem;
                        text-align: center;
                        font-weight: 600;
                        font-size: 0.95rem;
                        box-shadow: 0 2px 6px rgba(32,70,201,0.25);
                    ">● {label}</div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                prefix = "✓ " if i < active else ""
                if st.button(
                    f"{prefix}{label}",
                    key=f"step_nav_{i}",
                    use_container_width=True,
                ):
                    st.session_state[STATE_STEP] = i
                    st.rerun()


def _render_wizard_step() -> None:
    inputs = st.session_state[STATE_INPUTS]
    step = st.session_state[STATE_STEP]
    _step_header()

    # Append a per-session nonce to widget keys so any preset/reset change
    # bumps the nonce and the next render re-creates the widgets from
    # `value=` (instead of restoring stale widget state).
    nonce = int(st.session_state.get(STATE_FORM_NONCE, 0))
    if step == 0:
        new = fh.step_project(inputs, key_prefix=f"p1_n{nonce}")
    elif step == 1:
        new = fh.step_production(inputs, key_prefix=f"p2_n{nonce}")
    else:
        new = fh.step_talent(inputs, key_prefix=f"p3_n{nonce}")
    # update inputs in session
    st.session_state[STATE_INPUTS] = {**inputs, **new}

    c_prev, c_spacer, c_next = st.columns([1, 4, 1])
    with c_prev:
        if step > 0:
            if st.button("← " + t("btn_back"), use_container_width=True):
                st.session_state[STATE_STEP] = step - 1
                st.rerun()
    with c_next:
        if step < 2:
            if st.button(t("btn_next") + " →", use_container_width=True, type="primary"):
                st.session_state[STATE_STEP] = step + 1
                st.rerun()
        else:
            if st.button(t("btn_predict"), use_container_width=True, type="primary"):
                _run_prediction()
                st.rerun()


def _run_prediction() -> None:
    try:
        from inference import predict_movie_profile
        inputs = st.session_state[STATE_INPUTS]
        result = predict_movie_profile(inputs)
        st.session_state[STATE_RESULT] = result
        st.session_state[STATE_LAST_RUN_INPUTS] = dict(inputs)
    except Exception as exc:
        st.session_state[STATE_RESULT] = {"error": str(exc)}


def _render_results() -> None:
    result = st.session_state.get(STATE_RESULT)
    inputs = st.session_state.get(STATE_LAST_RUN_INPUTS, st.session_state[STATE_INPUTS])
    if not result:
        return
    if "error" in result:
        st.error(f"Prediction failed: {result['error']}")
        return

    outcome = str(result.get("prediction", "")).lower()
    confidence = float(result.get("confidence", 0.0))
    probabilities = result.get("probabilities", {})
    hit_p = float(probabilities.get("hit", 0.0))

    from ui_styles import CLASS_COLORS

    uc.section_title(t("result_title"))

    # Premium result hero: outcome badge + hit-score donut + probabilities Plotly
    col_badge, col_donut, col_probs = st.columns([1.2, 1.1, 2])
    with col_badge:
        st.markdown(uc.outcome_badge(outcome), unsafe_allow_html=True)
        st.caption(t("result_outcome"))
        st.markdown(f"### {_outcome_i18n(outcome)}")
        st.caption(_risk_to_i18n(result.get("risk_level", "")))
    with col_donut:
        donut = uc.confidence_donut(
            hit_p,
            label=t("result_hit_score"),
            color=CLASS_COLORS.get(outcome, CLASS_COLORS["hit"]),
        )
        st.plotly_chart(donut, use_container_width=True, config={"displayModeBar": False})
        st.caption(t("result_hit_score_desc"))
    with col_probs:
        st.caption(t("result_probabilities"))
        bars = uc.probability_bars_plotly(probabilities)
        st.plotly_chart(bars, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            f"{t('result_confidence')}: **{confidence * 100:.1f}%**"
        )

    uc.section_title(t("result_interpretation"))
    st.markdown(_business_i18n(outcome, confidence))

    uc.section_title(t("result_drivers_title"))
    uc.driver_pills(fh.compute_drivers(inputs))

    # Sensitivity
    uc.section_title(t("result_sensitivity_title"))
    st.caption(t("result_sensitivity_help"))
    try:
        from sensitivity import run_sensitivity, to_display_rows
        base_p_hit = float(probabilities.get("hit", 0.0))
        sens_results = run_sensitivity(inputs, base_p_hit)
        rows = to_display_rows(sens_results)
        if rows:
            uc.sensitivity_table(rows)
        else:
            st.caption(t("common_no_data"))
    except Exception as exc:
        st.warning(f"Sensitivity analysis unavailable: {exc}")
        rows = []

    # Comparables
    uc.section_title(t("result_comparables_title"))
    st.caption(t("result_comparables_help"))
    comparables_df = None
    try:
        from comparables import find_comparables
        enriched_inputs = fh.add_release_season(inputs)
        comparables_df = find_comparables(enriched_inputs, k=3)
        if comparables_df is not None and not comparables_df.empty:
            cc = st.columns(3)
            for col, (_, row) in zip(cc, comparables_df.iterrows()):
                with col:
                    uc.comparable_card(row, float(row.get("similarity", 0.0)))
        else:
            st.caption(t("common_no_data"))
    except Exception as exc:
        st.caption(f"{t('common_no_data')} ({exc})")

    # Export
    uc.section_title(t("result_export_title"))
    project_name = st.session_state.get(STATE_NAME) or "Untitled project"

    c_pdf, c_json, _ = st.columns([1, 1, 3])
    with c_pdf:
        try:
            from report_pdf import build_report_pdf
            from ui_styles import get_lang
            pdf_bytes = build_report_pdf(
                project_name=project_name,
                user_inputs=inputs,
                prediction=result,
                drivers=[label for label, _ in fh.compute_drivers(inputs)],
                sensitivity_rows=rows,
                comparables=comparables_df,
                lang=get_lang(),
            )
            st.download_button(
                "⬇ " + t("result_export_pdf"),
                data=pdf_bytes,
                file_name=f"cinesignal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.caption(f"PDF unavailable: {exc}")
    with c_json:
        json_blob = json.dumps(
            {
                "project_name": project_name,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "inputs": {k: v for k, v in inputs.items() if not isinstance(v, (bytes, bytearray))},
                "prediction": result,
            },
            indent=2,
            default=str,
        )
        st.download_button(
            "⬇ " + t("result_export_json"),
            data=json_blob,
            file_name=f"cinesignal_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )


def render() -> None:
    _init_state()

    # Demo case auto-fill from Dashboard
    if st.session_state.pop("_auto_run_predict", False):
        _run_prediction()

    st.title(t("predict_title"))
    st.caption(t("predict_subtitle"))

    # Top bar: project name + preset + reset
    c_name, c_preset, c_reset = st.columns([3, 2, 1])
    with c_name:
        st.session_state[STATE_NAME] = st.text_input(
            "🎬 " + t("compare_name"),
            value=st.session_state.get(STATE_NAME, ""),
            placeholder="My next blockbuster",
            label_visibility="visible",
        )
    with c_preset:
        preset_keys = fh.preset_options(include_custom=True)
        cur_preset = st.session_state.get(STATE_PRESET, "preset_custom")
        if cur_preset not in preset_keys:
            cur_preset = "preset_custom"
        # The widget key holds the user-visible choice. We sync it to the
        # canonical STATE_PRESET so external code (Dashboard demo cards) can
        # also drive this selectbox programmatically.
        if st.session_state.get("predict_preset_selector") != cur_preset:
            st.session_state["predict_preset_selector"] = cur_preset
        st.selectbox(
            t("preset_label"),
            preset_keys,
            format_func=fh.preset_label,
            key="predict_preset_selector",
            on_change=_on_preset_changed,
        )
    with c_reset:
        st.write("")
        st.write("")
        if st.button("↺ " + t("btn_reset"), use_container_width=True):
            _reset_form()
            st.rerun()

    # Wizard or results
    if st.session_state.get(STATE_RESULT) and "error" not in st.session_state[STATE_RESULT]:
        _render_wizard_step()
        st.markdown("---")
        _render_results()
    else:
        _render_wizard_step()
        if st.session_state.get(STATE_RESULT) and "error" in st.session_state[STATE_RESULT]:
            st.error(st.session_state[STATE_RESULT]["error"])
