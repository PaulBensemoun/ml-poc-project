"""Reusable UI components for the Movie Success Predictor app."""

from __future__ import annotations

import inspect
from typing import Any, Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui_styles import CLASS_COLORS, CLASS_COLORS_PLOTLY, ICONS, LOGO_SVG, PALETTE, t


def hero(title: str, body: str, stats: list[tuple[str, str]] | None = None) -> None:
    """Premium hero with optional stat strip embedded.

    stats: list of (value, label).
    """
    stats_html = ""
    if stats:
        items = "".join(
            f'<div class="hero-stat"><div class="v">{v}</div><div class="l">{lab}</div></div>'
            for v, lab in stats
        )
        stats_html = f'<div class="hero-stat-row">{items}</div>'
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{body}</p>
            {stats_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_strip(items: list[tuple[str, str]]) -> None:
    """Horizontal stat strip — list of (label, value)."""
    parts = "".join(
        f'<div class="stat-strip-item">'
        f'<div class="stat-strip-label">{label}</div>'
        f'<div class="stat-strip-value">{value}</div>'
        f"</div>"
        for label, value in items
    )
    st.markdown(f'<div class="stat-strip">{parts}</div>', unsafe_allow_html=True)


def demo_card(emoji: str, title: str, description: str, tags: list[str]) -> None:
    tags_html = "".join(f'<span class="demo-tag">{tag}</span>' for tag in tags)
    st.markdown(
        f"""
        <div class="demo-card">
            <div class="demo-emoji">{emoji}</div>
            <div class="demo-title">{title}</div>
            <div class="demo-desc">{description}</div>
            <div class="demo-tags">{tags_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def onboarding_banner(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="onboarding">
            <div class="onboarding-text"><strong>👋 {title}</strong> — {body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def confidence_donut(value: float, label: str = "Confidence", color: str | None = None) -> go.Figure:
    """Big donut showing a single probability (0-1) as a percentage."""
    color = color or PALETTE["accent"]
    v = max(0.0, min(1.0, float(value))) * 100
    fig = go.Figure(
        go.Pie(
            values=[v, 100 - v],
            labels=["", ""],
            hole=0.78,
            sort=False,
            direction="clockwise",
            marker=dict(colors=[color, "#F1F5F9"]),
            textinfo="none",
            hovertemplate=f"{label}: %{{value:.1f}}%<extra></extra>",
        )
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=240,
        annotations=[
            dict(
                text=f"<b style='font-size:2rem;color:{PALETTE['text']};'>{v:.0f}</b>"
                     f"<span style='font-size:1.05rem;color:{PALETTE['muted_soft']};'>/100</span><br/>"
                     f"<span style='font-size:0.7rem;color:{PALETTE['muted']};letter-spacing:0.04em;text-transform:uppercase'>{label}</span>",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
        ],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def probability_bars_plotly(probabilities: dict[str, float], height: int = 220) -> go.Figure:
    """Horizontal bar chart with class colours, Plotly-rendered."""
    order = ["flop", "average", "hit"]
    labels = [c.capitalize() for c in order]
    values = [float(probabilities.get(c, 0.0)) * 100 for c in order]
    colors = [CLASS_COLORS_PLOTLY[c] for c in order]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v:.1f}%" for v in values],
            textposition="auto",
            textfont=dict(color="white", size=13, family="Inter,sans-serif"),
            hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#F1F5F9", showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=13, color=PALETTE["text"])),
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.35,
    )
    return fig


def _outcome_label(outcome: str) -> str:
    return {
        "hit": ICONS["hit"] + " " + t("outcome_hit"),
        "average": ICONS["average"] + " " + t("outcome_average"),
        "flop": ICONS["flop"] + " " + t("outcome_flop"),
    }.get(outcome.lower(), outcome.upper())


def class_distribution_donut(counts: dict[str, int], height: int = 280) -> go.Figure:
    order = ["flop", "average", "hit"]
    labels = [c.capitalize() for c in order if c in counts]
    values = [counts.get(c, 0) for c in order if c in counts]
    colors = [CLASS_COLORS_PLOTLY[c] for c in order if c in counts]
    fig = go.Figure(
        go.Pie(
            values=values,
            labels=labels,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="white", width=2)),
            textinfo="label+percent",
            textfont=dict(size=12, color=PALETTE["text"]),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def kpi_card(
    label: str,
    value: str,
    sub: str | None = None,
    variant: str = "accent",
) -> None:
    variant_class = {
        "accent": "card-accent",
        "success": "card-success",
        "warning": "card-warning",
        "danger": "card-danger",
        "plain": "",
    }.get(variant, "card-accent")
    sub_html = f'<div class="card-sub">{sub}</div>' if sub else ""
    st.markdown(
        f"""
        <div class="card {variant_class}">
            <div class="card-title">{label}</div>
            <div class="card-value">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def outcome_badge(label: str) -> str:
    key = str(label).lower().strip()
    css = {"hit": "outcome-hit", "average": "outcome-average", "flop": "outcome-flop"}.get(key, "outcome-average")
    return f'<span class="outcome {css}"><span class="dot" style="background:{CLASS_COLORS.get(key, PALETTE["muted"])}"></span>{label.upper()}</span>'


def probability_bar(label: str, value: float, css_class: str) -> str:
    pct = max(0.0, min(1.0, float(value)))
    width = pct * 100
    return f"""
    <div class="probability-row">
        <div class="label">{label}</div>
        <div class="track"><div class="fill {css_class}" style="width:{width:.1f}%"></div></div>
        <div class="value">{pct * 100:.1f}%</div>
    </div>
    """


def probability_block(probabilities: dict[str, float]) -> None:
    rows = ""
    order = [("flop", "fill-flop"), ("average", "fill-average"), ("hit", "fill-hit")]
    label_map = {"flop": "Flop", "average": t("kpi_movies") and "Average" or "Average", "hit": "Hit"}
    # use clean static labels (no i18n surprise)
    label_map = {"flop": "Flop", "average": "Average", "hit": "Hit"}
    for cls, css_cls in order:
        p = float(probabilities.get(cls, 0.0))
        rows += probability_bar(label_map[cls], p, css_cls)
    st.markdown(rows, unsafe_allow_html=True)


def insight_box(title: str, body: str, kind: str = "info") -> None:
    css = {"info": "", "warn": "insight-warn", "success": "insight-success"}.get(kind, "")
    st.markdown(
        f"""
        <div class="insight {css}">
            <div class="insight-title">{title}</div>
            <div class="insight-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def driver_pills(items: Iterable[tuple[str, str]]) -> None:
    """Render driver pills.

    Each item is (label, direction) where direction in {'up', 'down', 'neutral'}.
    """
    html_parts = []
    for label, direction in items:
        cls = {"up": "driver-up", "down": "driver-down"}.get(direction, "driver-neutral")
        html_parts.append(f'<span class="driver-pill {cls}">{label}</span>')
    st.markdown(" ".join(html_parts) or "—", unsafe_allow_html=True)


def steps_indicator(labels: list[str], active: int) -> None:
    parts = []
    for i, label in enumerate(labels):
        if i == active:
            cls = "active"
        elif i < active:
            cls = "done"
        else:
            cls = ""
        parts.append(f'<div class="step {cls}">{label}</div>')
    st.markdown(f'<div class="steps">{"".join(parts)}</div>', unsafe_allow_html=True)


def comparable_card(row: pd.Series, similarity: float) -> None:
    title = str(row.get("title", "—"))
    outcome = str(row.get("movie_success_class", "—"))
    budget = row.get("budget")
    revenue = row.get("revenue")
    runtime = row.get("runtime")
    genre = row.get("main_genre", "—")
    year = row.get("release_year")
    director = row.get("director_name", "—")
    cast_size = row.get("cast_size")

    def _money(v: Any) -> str:
        if v is None or pd.isna(v) or float(v) == 0:
            return "—"
        v = float(v)
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"

    badge = outcome_badge(outcome)
    sim_pct = max(0.0, min(1.0, float(similarity))) * 100
    year_s = f" · {int(year)}" if year is not None and pd.notna(year) else ""
    director_s = "" if str(director) == "__missing__" else f"<br/>🎬 {director}"
    st.markdown(
        f"""
        <div class="comp-card">
            <div class="comp-title">{title}{year_s}</div>
            <div style="margin-bottom:0.4rem;">{badge}</div>
            <div class="comp-meta">
                <strong>Genre:</strong> {genre} ·
                <strong>Runtime:</strong> {int(runtime) if runtime is not None and pd.notna(runtime) else '—'} min<br/>
                <strong>Budget:</strong> {_money(budget)} ·
                <strong>Revenue:</strong> {_money(revenue)}<br/>
                <strong>Cast size:</strong> {int(cast_size) if cast_size is not None and pd.notna(cast_size) else '—'}{director_s}
            </div>
            <div class="comp-similarity">Similarity: {sim_pct:.0f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sensitivity_row(label: str, delta_pp: float, new_p_hit: float) -> str:
    if delta_pp > 0.5:
        delta_cls = "sens-delta-up"
    elif delta_pp < -0.5:
        delta_cls = "sens-delta-down"
    else:
        delta_cls = "sens-delta-flat"
    # The "+" format-specifier already adds the sign, so we do NOT prepend
    # another "+" — avoids the "++3.2 pp" double-sign rendering.
    # NOTE: do NOT indent the inner HTML — Markdown treats 4+ leading spaces as a code block,
    # which would surface the raw HTML to the user (only the first row would render).
    return (
        f'<div class="sens-row">'
        f'<div class="sens-label">{label}</div>'
        f'<div>'
        f'<span style="color:#475569;margin-right:0.8rem;">P(hit) → {new_p_hit*100:.1f}%</span>'
        f'<span class="{delta_cls}">{delta_pp:+.1f} pp</span>'
        f'</div>'
        f'</div>'
    )


def sensitivity_table(rows: list[tuple[str, float, float]]) -> None:
    """rows = list of (label, delta_pp, new_p_hit)."""
    body = "".join(sensitivity_row(lbl, d, p) for lbl, d, p in rows)
    st.markdown(f'<div class="card">{body}</div>', unsafe_allow_html=True)


def image_responsive(path: str, caption: str | None = None) -> None:
    params = inspect.signature(st.image).parameters
    kw: dict[str, Any] = {}
    if "use_container_width" in params:
        kw["use_container_width"] = True
    elif "use_column_width" in params:
        kw["use_column_width"] = True
    if caption:
        kw["caption"] = caption
    st.image(path, **kw)


def dataframe_clean(df: pd.DataFrame, **kwargs: Any) -> None:
    params = inspect.signature(st.dataframe).parameters
    opts = dict(kwargs)
    if "hide_index" in params:
        opts.setdefault("hide_index", True)
    if "use_container_width" in params:
        opts.setdefault("use_container_width", True)
    elif "use_column_width" in params:
        opts["use_column_width"] = True
    st.dataframe(df, **opts)
