"""Insights page — interactive Plotly analytics from the processed corpus.

Replaces the previous static-PNG layout with live filters + Plotly charts
so the audience can explore the data instead of just reading captions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
import ui_components as uc
from ui_styles import CLASS_COLORS_PLOTLY, PALETTE, t


GENRE_DISPLAY_ORDER = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "Thriller", "War", "Western",
]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
CLASS_ORDER = ["flop", "average", "hit"]


@st.cache_data(show_spinner=False)
def _load_corpus() -> pd.DataFrame:
    path = config.PROCESSED_MOVIES_CSV
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "movie_success_class" in df.columns:
        df["movie_success_class"] = df["movie_success_class"].astype("string")
    if "release_year" in df.columns:
        df["decade"] = (df["release_year"] // 10 * 10).astype("Int64")
    return df


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()

    genres = st.session_state.get("ins_genres", [])
    decades = st.session_state.get("ins_decades", [])
    classes = st.session_state.get("ins_classes", [])

    if genres and "main_genre" in out.columns:
        out = out[out["main_genre"].isin(genres)]
    if decades and "decade" in out.columns:
        out = out[out["decade"].isin(decades)]
    if classes and "movie_success_class" in out.columns:
        out = out[out["movie_success_class"].isin(classes)]
    return out


def _filter_bar(df: pd.DataFrame) -> None:
    if df.empty:
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        if "main_genre" in df.columns:
            genres = sorted([g for g in df["main_genre"].dropna().unique().tolist() if isinstance(g, str)])
            st.multiselect(
                t("insights_filter_genre"),
                genres,
                key="ins_genres",
                placeholder=t("common_search"),
            )
    with c2:
        if "decade" in df.columns:
            decs = sorted([int(d) for d in df["decade"].dropna().unique().tolist()])
            st.multiselect(
                t("insights_filter_decade"),
                decs,
                key="ins_decades",
                format_func=lambda d: f"{d}s",
            )
    with c3:
        if "movie_success_class" in df.columns:
            classes = ["flop", "average", "hit"]
            st.multiselect(
                t("insights_filter_class"),
                classes,
                key="ins_classes",
                format_func=lambda c: c.capitalize(),
            )


def _kpi_strip(df: pd.DataFrame) -> None:
    n = len(df)
    hit_rate = 0.0
    if n and "movie_success_class" in df.columns:
        hit_rate = float((df["movie_success_class"] == "hit").mean()) * 100
    med_budget = float(df["budget"].median()) if "budget" in df.columns and n else 0
    med_roi = float(df["roi"].median()) if "roi" in df.columns and n else 0

    def _fmt_budget(v: float) -> str:
        if v >= 1_000_000_000: return f"${v/1_000_000_000:.1f}B"
        if v >= 1_000_000: return f"${v/1_000_000:.0f}M"
        if v >= 1_000: return f"${v/1_000:.0f}K"
        return f"${v:.0f}"

    uc.stat_strip(
        [
            (t("insights_kpi_films"), f"{n:,}"),
            (t("insights_kpi_hit_rate"), f"{hit_rate:.1f}%"),
            (t("insights_kpi_avg_budget"), _fmt_budget(med_budget) if med_budget else "—"),
            (t("insights_kpi_avg_roi"), f"{med_roi:.2f}x" if med_roi else "—"),
        ]
    )


def _chart_class_volume(df: pd.DataFrame) -> go.Figure:
    counts = df["movie_success_class"].value_counts().to_dict() if "movie_success_class" in df.columns else {}
    labels = [c.capitalize() for c in CLASS_ORDER]
    values = [counts.get(c, 0) for c in CLASS_ORDER]
    colors = [CLASS_COLORS_PLOTLY[c] for c in CLASS_ORDER]
    fig = go.Figure(
        go.Bar(
            x=labels, y=values, marker=dict(color=colors), text=values, textposition="outside",
            hovertemplate="%{x}: %{y} films<extra></extra>",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=20, b=20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        yaxis=dict(gridcolor="#F1F5F9"),
        title=dict(text=t("insights_chart_class_volume"), x=0, font=dict(size=14)),
    )
    return fig


def _chart_budget_roi(df: pd.DataFrame) -> go.Figure | None:
    if "budget" not in df.columns or "roi" not in df.columns:
        return None
    plot_df = df.dropna(subset=["budget", "roi"]).copy()
    plot_df = plot_df[(plot_df["budget"] > 0) & (plot_df["roi"] > 0)]
    if plot_df.empty:
        return None
    plot_df["log_budget"] = np.log10(plot_df["budget"])
    plot_df["log_roi"] = np.log10(plot_df["roi"])
    color_col = "movie_success_class" if "movie_success_class" in plot_df.columns else None
    fig = px.scatter(
        plot_df.sample(min(2000, len(plot_df)), random_state=42),
        x="log_budget", y="log_roi",
        color=color_col,
        color_discrete_map={k: v for k, v in CLASS_COLORS_PLOTLY.items()},
        hover_data={"title": True, "budget": ":.0f", "roi": ":.2f", "log_budget": False, "log_roi": False}
        if "title" in plot_df.columns
        else {"budget": ":.0f", "roi": ":.2f", "log_budget": False, "log_roi": False},
        opacity=0.7,
        labels={"log_budget": "log10(Budget)", "log_roi": "log10(ROI)", "movie_success_class": "Class"},
    )
    fig.update_traces(marker=dict(size=6))
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=t("insights_chart_budget_roi"), x=0, font=dict(size=14)),
        legend=dict(orientation="h", y=1.06),
        xaxis=dict(gridcolor="#F1F5F9"),
        yaxis=dict(gridcolor="#F1F5F9"),
    )
    return fig


def _chart_genre_class(df: pd.DataFrame) -> go.Figure | None:
    if "main_genre" not in df.columns or "movie_success_class" not in df.columns:
        return None
    grp = (
        df.groupby(["main_genre", "movie_success_class"]).size().reset_index(name="n")
    )
    pivot = grp.pivot(index="main_genre", columns="movie_success_class", values="n").fillna(0)
    pivot["total"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("total", ascending=True)
    fig = go.Figure()
    for cls in CLASS_ORDER:
        if cls in pivot.columns:
            fig.add_trace(
                go.Bar(
                    y=pivot.index.tolist(),
                    x=(pivot[cls] / pivot["total"] * 100).tolist(),
                    orientation="h",
                    name=cls.capitalize(),
                    marker=dict(color=CLASS_COLORS_PLOTLY[cls]),
                    hovertemplate="<b>%{y}</b><br>" + cls.capitalize() + ": %{x:.1f}%<extra></extra>",
                )
            )
    fig.update_layout(
        barmode="stack",
        height=max(380, 18 * len(pivot)),
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        title=dict(text=t("insights_chart_genre_class") + " (%)", x=0, font=dict(size=14)),
        xaxis=dict(range=[0, 100], gridcolor="#F1F5F9", ticksuffix="%"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", y=1.04),
    )
    return fig


def _chart_month_roi(df: pd.DataFrame) -> go.Figure | None:
    if "release_month" not in df.columns or "roi" not in df.columns:
        return None
    plot_df = df.dropna(subset=["release_month", "roi"]).copy()
    plot_df["release_month"] = plot_df["release_month"].astype(int)
    monthly = plot_df.groupby("release_month")["roi"].median().reindex(range(1, 13))
    fig = go.Figure(
        go.Bar(
            x=MONTH_LABELS,
            y=monthly.values,
            marker=dict(color=PALETTE["accent"]),
            text=[f"{v:.2f}x" if pd.notna(v) else "—" for v in monthly.values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Median ROI: %{y:.2f}x<extra></extra>",
        )
    )
    fig.update_layout(
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title=dict(text=t("insights_chart_month_roi"), x=0, font=dict(size=14)),
        yaxis=dict(gridcolor="#F1F5F9"),
    )
    return fig


def _chart_decade_hit(df: pd.DataFrame) -> go.Figure | None:
    if "decade" not in df.columns or "movie_success_class" not in df.columns:
        return None
    grouped = df.dropna(subset=["decade"]).groupby("decade")
    decades = []
    hit_rates = []
    counts = []
    for dec, g in grouped:
        if len(g) < 5:
            continue
        decades.append(int(dec))
        hit_rates.append((g["movie_success_class"] == "hit").mean() * 100)
        counts.append(len(g))
    if not decades:
        return None
    fig = go.Figure(
        go.Scatter(
            x=[f"{d}s" for d in decades],
            y=hit_rates,
            mode="lines+markers",
            line=dict(color=PALETTE["accent"], width=3),
            marker=dict(size=10, color=PALETTE["primary"]),
            text=[f"{c} films" for c in counts],
            hovertemplate="<b>%{x}</b><br>Hit rate: %{y:.1f}%<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        title=dict(text=t("insights_chart_decade_hit"), x=0, font=dict(size=14)),
        yaxis=dict(gridcolor="#F1F5F9", ticksuffix="%"),
    )
    return fig


def render() -> None:
    st.title(t("insights_title"))
    st.caption(t("insights_subtitle"))

    df = _load_corpus()
    if df.empty:
        st.warning(t("common_no_data"))
        return

    _filter_bar(df)
    filtered = _apply_filters(df)
    _kpi_strip(filtered)

    st.write("")
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.plotly_chart(_chart_class_volume(filtered), use_container_width=True, config={"displayModeBar": False})
        st.caption(t("insights_caption_class_volume"))
    with c2:
        fig = _chart_budget_roi(filtered)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption(t("insights_caption_budget_roi"))

    fig_g = _chart_genre_class(filtered)
    if fig_g:
        st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})
        st.caption(t("insights_caption_genre_class"))

    c3, c4 = st.columns(2)
    with c3:
        fig_m = _chart_month_roi(filtered)
        if fig_m:
            st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar": False})
            st.caption(t("insights_caption_month_roi"))
    with c4:
        fig_d = _chart_decade_hit(filtered)
        if fig_d:
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})
            st.caption(t("insights_caption_decade_hit"))

    uc.insight_box(
        t("insights_tab_credits"),
        (
            "Le ROI plafonne pour les blockbusters et explose pour des budgets faibles "
            "(horreur, niche). Les sorties estivales/holidays dominent. Le mix d'issues "
            "par genre est très contrasté."
        ),
        kind="info",
    )
