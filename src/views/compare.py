"""Compare page — run up to 4 scenarios side-by-side."""

from __future__ import annotations

import copy
from typing import Any

import pandas as pd
import streamlit as st

import form_helpers as fh
import ui_components as uc
from ui_styles import t


MAX_SCENARIOS = 4
STATE_SCENARIOS = "compare_scenarios"
STATE_RESULTS = "compare_results"
STATE_FORM_NONCES = "compare_form_nonces"  # scenario_idx → int nonce


def _init_state() -> None:
    if STATE_SCENARIOS not in st.session_state:
        base = fh.empty_defaults()
        base.update(fh.model_input_defaults())
        st.session_state[STATE_SCENARIOS] = [
            {"name": "Scenario A", "inputs": copy.deepcopy(base), "preset": "preset_custom"},
            {"name": "Scenario B", "inputs": copy.deepcopy(base), "preset": "preset_custom"},
        ]


def _remove_widget_keys(scenario_idx: int) -> None:
    """Drop all Streamlit widget keys for one scenario (any nonce generation)."""
    prefix = f"sc{scenario_idx}_"
    for key in list(st.session_state.keys()):
        if key.startswith(prefix):
            del st.session_state[key]


def _get_form_nonce(scenario_idx: int) -> int:
    nonces = st.session_state.setdefault(STATE_FORM_NONCES, {})
    return int(nonces.get(scenario_idx, 0))


def _bump_form_nonce(scenario_idx: int) -> None:
    nonces = st.session_state.setdefault(STATE_FORM_NONCES, {})
    nonces[scenario_idx] = int(nonces.get(scenario_idx, 0)) + 1
    st.session_state[STATE_FORM_NONCES] = nonces


def _apply_preset_to_scenario(scenario_idx: int, preset_key: str) -> None:
    """Apply a project template to one scenario and force widgets to rebuild."""
    scenarios = st.session_state[STATE_SCENARIOS]
    if preset_key != "preset_custom" and preset_key in fh.PRESETS:
        base = fh.empty_defaults()
        base.update(fh.model_input_defaults())
        base.update(fh.PRESETS[preset_key])
        scenarios[scenario_idx]["inputs"] = copy.deepcopy(base)
        _remove_widget_keys(scenario_idx)
        _bump_form_nonce(scenario_idx)
    scenarios[scenario_idx]["preset"] = preset_key
    st.session_state[STATE_SCENARIOS] = scenarios
    # Stale comparison — user must re-run after changing a template
    st.session_state.pop(STATE_RESULTS, None)


def _on_preset_changed(scenario_idx: int) -> None:
    """Selectbox on_change: apply template before the automatic rerun."""
    widget_key = f"sc{scenario_idx}_preset"
    new_choice = st.session_state.get(widget_key)
    scenarios = st.session_state.get(STATE_SCENARIOS, [])
    if not new_choice or scenario_idx >= len(scenarios):
        return
    if new_choice != scenarios[scenario_idx].get("preset"):
        _apply_preset_to_scenario(scenario_idx, new_choice)


def _add_scenario() -> None:
    scenarios = st.session_state[STATE_SCENARIOS]
    if len(scenarios) >= MAX_SCENARIOS:
        st.warning(t("compare_max"))
        return
    base = fh.empty_defaults()
    base.update(fh.model_input_defaults())
    label = chr(ord("A") + len(scenarios))
    new_idx = len(scenarios)
    scenarios.append({"name": f"Scenario {label}", "inputs": copy.deepcopy(base), "preset": "preset_custom"})
    st.session_state[STATE_SCENARIOS] = scenarios
    nonces = st.session_state.setdefault(STATE_FORM_NONCES, {})
    nonces[new_idx] = 0
    st.session_state[STATE_FORM_NONCES] = nonces
    st.session_state.pop(STATE_RESULTS, None)


def _remove_scenario(idx: int) -> None:
    scenarios = st.session_state[STATE_SCENARIOS]
    if len(scenarios) <= 1:
        return
    scenarios.pop(idx)
    st.session_state[STATE_SCENARIOS] = scenarios
    _remove_widget_keys(idx)
    st.session_state.pop(STATE_RESULTS, None)


def _scenario_editor(scenario_idx: int) -> None:
    scenarios = st.session_state[STATE_SCENARIOS]
    sc = scenarios[scenario_idx]
    prefix = f"sc{scenario_idx}"

    c_name, c_preset, c_remove = st.columns([3, 2, 1])
    with c_name:
        sc["name"] = st.text_input(
            t("compare_name"),
            value=sc.get("name", f"Scenario {scenario_idx + 1}"),
            key=f"{prefix}_name",
        )
    with c_preset:
        preset_keys = fh.preset_options(include_custom=True)
        cur = sc.get("preset", "preset_custom")
        if cur not in preset_keys:
            cur = "preset_custom"
        preset_widget_key = f"{prefix}_preset"
        if st.session_state.get(preset_widget_key) != cur:
            st.session_state[preset_widget_key] = cur
        st.selectbox(
            t("preset_label"),
            preset_keys,
            format_func=fh.preset_label,
            key=preset_widget_key,
            on_change=_on_preset_changed,
            args=(scenario_idx,),
        )
    with c_remove:
        st.write("")
        st.write("")
        if len(scenarios) > 1:
            if st.button("✕ " + t("compare_remove"), key=f"{prefix}_remove", use_container_width=True):
                _remove_scenario(scenario_idx)
                st.rerun()

    # Nonce in the prefix forces new widget keys after each template change
    form_prefix = f"{prefix}_n{_get_form_nonce(scenario_idx)}"
    new_inputs = fh.render_compact_form(sc["inputs"], key_prefix=form_prefix)
    sc["inputs"] = {**sc["inputs"], **new_inputs}
    scenarios[scenario_idx] = sc
    st.session_state[STATE_SCENARIOS] = scenarios


def _run_comparison() -> None:
    try:
        from inference import predict_movie_profile
    except Exception as exc:
        st.error(f"Model unavailable: {exc}")
        return

    scenarios = st.session_state[STATE_SCENARIOS]
    results = []
    for sc in scenarios:
        try:
            out = predict_movie_profile(sc["inputs"])
            results.append({"name": sc["name"], "result": out, "error": None})
        except Exception as exc:
            results.append({"name": sc["name"], "result": None, "error": str(exc)})
    st.session_state[STATE_RESULTS] = results


def _render_results() -> None:
    results = st.session_state.get(STATE_RESULTS)
    if not results:
        return

    uc.section_title(t("compare_summary"))

    # Identify winner (highest p_hit)
    valid = [r for r in results if r["error"] is None and r["result"]]
    winner_idx: int | None = None
    if valid:
        winner = max(valid, key=lambda r: r["result"]["probabilities"].get("hit", 0))
        winner_idx = results.index(winner)

    # 1) Score strip (always visible at top, big numbers)
    score_items = []
    for i, item in enumerate(results):
        if item["error"]:
            continue
        res = item["result"]
        hit_p = float(res.get("probabilities", {}).get("hit", 0.0)) * 100
        label = item["name"]
        if i == winner_idx:
            label = "★ " + label
        score_items.append((label, f"{hit_p:.0f}%"))
    if score_items:
        uc.stat_strip(score_items)

    st.write("")

    # 2) Side-by-side columns (sticky headers + result cards)
    cols = st.columns(len(results))
    for i, (col, item) in enumerate(zip(cols, results)):
        with col:
            if item["error"] is not None:
                st.error(f"{item['name']}: {item['error']}")
                continue
            res = item["result"]
            outcome = str(res.get("prediction", "")).lower()
            conf = float(res.get("confidence", 0.0))
            probs = res.get("probabilities", {})
            hit_p = float(probs.get("hit", 0.0))

            header_class = "compare-col-header winner" if i == winner_idx else "compare-col-header"
            badge = " ★" if i == winner_idx else ""
            st.markdown(
                f'<div class="{header_class}">{item["name"]}{badge}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="compare-result">'
                f'<div class="name">{uc._outcome_label(outcome)}</div>',
                unsafe_allow_html=True,
            )
            from ui_styles import CLASS_COLORS
            st.plotly_chart(
                uc.confidence_donut(
                    hit_p,
                    label=t("compare_winner_score"),
                    color=CLASS_COLORS.get(outcome),
                ),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"compare_donut_{i}",
            )
            st.plotly_chart(
                uc.probability_bars_plotly(probs, height=180),
                use_container_width=True,
                config={"displayModeBar": False},
                key=f"compare_bars_{i}",
            )
            st.caption(f"{t('result_confidence')}: {conf * 100:.1f}%")
            st.markdown("</div>", unsafe_allow_html=True)

    # 3) Compact summary table (collapsible)
    with st.expander(t("compare_summary") + " (table)", expanded=False):
        table_rows = []
        for item in results:
            if item["error"]:
                continue
            res = item["result"]
            probs = res["probabilities"]
            table_rows.append({
                t("compare_name"): item["name"],
                t("result_outcome"): str(res["prediction"]).upper(),
                t("result_confidence"): f"{res['confidence'] * 100:.1f}%",
                "P(flop)": f"{probs.get('flop', 0)*100:.1f}%",
                "P(average)": f"{probs.get('average', 0)*100:.1f}%",
                "P(hit)": f"{probs.get('hit', 0)*100:.1f}%",
            })
        if table_rows:
            uc.dataframe_clean(pd.DataFrame(table_rows))


def render() -> None:
    _init_state()

    st.title(t("compare_title"))
    st.caption(t("compare_subtitle"))

    scenarios = st.session_state[STATE_SCENARIOS]
    tab_labels = [t("compare_scenario", n=i + 1) for i in range(len(scenarios))]
    tabs = st.tabs(tab_labels)
    for i, tab in enumerate(tabs):
        with tab:
            _scenario_editor(i)

    st.markdown("---")
    c_add, c_run, _ = st.columns([1, 1, 3])
    with c_add:
        if st.button("➕ " + t("compare_add"), use_container_width=True, disabled=len(scenarios) >= MAX_SCENARIOS):
            _add_scenario()
            st.rerun()
    with c_run:
        if st.button("▶ " + t("compare_run"), use_container_width=True, type="primary"):
            if len(st.session_state[STATE_SCENARIOS]) < 2:
                st.warning(t("compare_empty"))
            else:
                _run_comparison()
                st.rerun()

    if st.session_state.get(STATE_RESULTS):
        st.markdown("---")
        _render_results()
