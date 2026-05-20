"""Shared helpers for the Streamlit dashboard."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import streamlit as st

from config import MODELS, PLOTS_DIR, TRAIN_ARTIFACTS_FILE

PLOTS_MODELING_DIR = PLOTS_DIR / "modeling"

CLASS_COLORS = {
    "hit": "#2d6a4f",
    "average": "#b08900",
    "flop": "#9b2226",
}


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }
        .hero-box {
            background: linear-gradient(135deg, #f8fafc 0%, #eef2f7 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.75rem 2rem;
            margin-bottom: 1.5rem;
        }
        .hero-box h1 { margin: 0 0 0.35rem 0; font-size: 1.85rem; color: #1a202c; }
        .hero-box p { margin: 0.35rem 0 0 0; color: #4a5568; line-height: 1.55; }
        .metric-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            min-height: 5.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .metric-card .label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #718096;
            margin-bottom: 0.35rem;
        }
        .metric-card .value {
            font-size: 1.45rem;
            font-weight: 600;
            color: #1a202c;
            line-height: 1.2;
        }
        .metric-card .subtitle {
            font-size: 0.82rem;
            color: #718096;
            margin-top: 0.4rem;
            line-height: 1.4;
        }
        .model-card {
            background: #ffffff;
            border: 1px solid #cbd5e0;
            border-left: 4px solid #2c5282;
            border-radius: 10px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 0.75rem;
        }
        .model-card .title { font-size: 0.78rem; text-transform: uppercase; color: #718096; }
        .model-card .name { font-size: 1.1rem; font-weight: 600; color: #1a202c; margin: 0.25rem 0; }
        .model-card .desc { font-size: 0.88rem; color: #4a5568; line-height: 1.45; }
        .use-case-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1rem 1.1rem;
            height: 100%;
        }
        .use-case-card h4 { margin: 0 0 0.5rem 0; color: #2d3748; font-size: 1rem; }
        .use-case-card p { margin: 0; color: #4a5568; font-size: 0.88rem; line-height: 1.45; }
        .insight-info {
            background: #ebf8ff;
            border: 1px solid #bee3f8;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            margin: 0.75rem 0;
        }
        .insight-warn {
            background: #fffaf0;
            border: 1px solid #fbd38d;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            margin: 0.75rem 0;
        }
        .insight-success {
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            margin: 0.75rem 0;
        }
        .insight-title { font-weight: 600; color: #2d3748; margin-bottom: 0.35rem; }
        .insight-body { color: #4a5568; font-size: 0.92rem; line-height: 1.5; }
        .risk-low { background: #fff5f5; border: 1px solid #feb2b2; border-radius: 10px; padding: 0.9rem 1rem; }
        .risk-medium { background: #fffaf0; border: 1px solid #fbd38d; border-radius: 10px; padding: 0.9rem 1rem; }
        .risk-high { background: #f0fff4; border: 1px solid #9ae6b4; border-radius: 10px; padding: 0.9rem 1rem; }
        .case-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 1rem 1.15rem;
            margin-bottom: 0.85rem;
        }
        .case-card .case-title { font-size: 1.05rem; font-weight: 600; color: #1a202c; margin-bottom: 0.5rem; }
        .case-meta { font-size: 0.84rem; color: #4a5568; line-height: 1.55; }
        .badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            text-transform: uppercase;
            margin-right: 0.35rem;
        }
        .badge-hit { background: #c6f6d5; color: #22543d; }
        .badge-average { background: #fefcbf; color: #744210; }
        .badge-flop { background: #fed7d7; color: #742a2a; }
        .badge-ok { background: #bee3f8; color: #2c5282; }
        .badge-rescue { background: #c6f6d5; color: #22543d; }
        .badge-risk { background: #fed7d7; color: #742a2a; }
        .section-title { font-size: 1.15rem; font-weight: 600; color: #2d3748; margin: 1.25rem 0 0.65rem 0; }
        .plot-takeaway {
            font-size: 0.88rem;
            color: #4a5568;
            font-style: italic;
            margin-top: -0.25rem;
            margin-bottom: 1rem;
        }
        .final-message {
            background: #f7fafc;
            border: 1px solid #cbd5e0;
            border-radius: 10px;
            padding: 1.25rem 1.5rem;
            margin-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_json(path_str: str) -> dict[str, Any] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def load_csv(path_str: str) -> pd.DataFrame | None:
    path = Path(path_str)
    if not path.exists():
        return None
    return pd.read_csv(path)


def get_plot_path(filename: str) -> Path:
    return PLOTS_MODELING_DIR / filename


def _image_width_kwarg() -> dict[str, bool]:
    params = inspect.signature(st.image).parameters
    if "use_container_width" in params:
        return {"use_container_width": True}
    if "use_column_width" in params:
        return {"use_column_width": True}
    return {}


def show_plot(filename: str, caption: str | None = None, takeaway: str | None = None) -> None:
    path = get_plot_path(filename)
    if path.exists():
        st.image(str(path), **_image_width_kwarg())
        if caption:
            st.caption(caption)
        if takeaway:
            st.markdown(f'<p class="plot-takeaway">{takeaway}</p>', unsafe_allow_html=True)
    else:
        st.warning(f"Plot not found: `{path.name}`. Run notebooks or check `plots/modeling/`.")


def format_pct(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{100 * float(value):.{decimals}f}%"


def format_num(value: float | None, decimals: int = 3) -> str:
    if value is None:
        return "—"
    return f"{float(value):.{decimals}f}"


def format_probability(value: float | None, decimals: int = 1) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return f"{100 * float(value):.{decimals}f}%"


def format_money_millions(value: float | None) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    v = float(value)
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:,.0f}"


READABLE_LABELS = {
    "y_true": "Actual",
    "y_pred_baseline": "Baseline prediction",
    "y_pred_credits": "Credits prediction",
    "delta_p_true": "Probability gain on true class",
    "p_true_baseline": "Baseline P(true class)",
    "p_true_credits": "Credits P(true class)",
    "base_confidence": "Baseline confidence",
    "confidence": "Credits confidence",
    "base_p_flop": "Baseline P(flop)",
    "base_p_average": "Baseline P(average)",
    "base_p_hit": "Baseline P(hit)",
    "p_flop": "Credits P(flop)",
    "p_average": "Credits P(average)",
    "p_hit": "Credits P(hit)",
    "main_genre": "Genre",
    "budget_bucket": "Budget bucket",
    "runtime_bucket": "Runtime bucket",
    "production_scale": "Production scale",
    "talent_score": "Talent score",
    "cast_size": "Cast size",
    "crew_size": "Crew size",
    "known_actor_count": "Known actors",
    "possible_franchise_flag": "Franchise flag",
    "director_name": "Director",
    "transition": "Transition",
}


def readable_label(column: str) -> str:
    return READABLE_LABELS.get(column, column.replace("_", " ").title())


TRANSITION_INTERPRETATIONS = {
    "stable_correct": "Both models agreed with the realized outcome.",
    "wrong_to_correct": "Credits features corrected the baseline prediction.",
    "correct_to_wrong": "Credits features introduced a regression; this is a governance warning.",
    "stable_wrong": "Both models missed the outcome; likely unobserved market factors matter.",
}


def transition_interpretation(transition: str) -> str:
    return TRANSITION_INTERPRETATIONS.get(
        str(transition), "Review probabilities and business context before acting on this signal."
    )


def rename_columns_readable(df: pd.DataFrame) -> pd.DataFrame:
    return df.rename(columns={c: readable_label(c) for c in df.columns if c in READABLE_LABELS})


SIMULATOR_PREFILL_KEYS = [
    "budget",
    "runtime",
    "main_genre",
    "original_language",
    "release_month",
    "release_quarter",
    "genre_count",
    "production_company_count",
    "production_country_count",
    "spoken_language_count",
    "cast_size",
    "crew_size",
    "writer_count",
    "director_name",
    "known_actor_count",
    "top_billed_cast_count",
    "possible_franchise_flag",
    "ensemble_cast_flag",
    "top_director_flag",
]


def row_to_simulator_prefill(row: pd.Series) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in SIMULATOR_PREFILL_KEYS:
        if key not in row.index:
            continue
        val = row[key]
        if pd.isna(val):
            continue
        if key in (
            "budget",
            "runtime",
            "release_month",
            "release_quarter",
            "genre_count",
            "production_company_count",
            "production_country_count",
            "spoken_language_count",
            "cast_size",
            "crew_size",
            "writer_count",
            "known_actor_count",
            "top_billed_cast_count",
            "possible_franchise_flag",
            "ensemble_cast_flag",
            "top_director_flag",
        ):
            try:
                out[key] = int(float(val))
            except (TypeError, ValueError):
                continue
        else:
            out[key] = str(val)
    dn = out.get("director_name", "")
    if dn in ("__other__", "nan"):
        out["director_name"] = "__missing__"
    return out


def get_director_names() -> list[str]:
    bundle = get_champion_bundle()
    if bundle is None:
        return []
    arts = bundle["artifacts"]
    names: set[str] = set()
    for key in ("director_bucket_top_names", "top_directors"):
        for n in arts.get(key, []):
            s = str(n).strip()
            if s and s not in ("__missing__", "__other__"):
                names.add(s)
    for n in arts.get("director_movie_count_map", {}):
        s = str(n).strip()
        if s and s not in ("__missing__", "__other__"):
            names.add(s)
    return sorted(names)


def _row_val(row: pd.Series, key: str, default: str = "—") -> str:
    if key not in row.index or pd.isna(row[key]):
        return default
    return str(row[key])


def movie_diagnostic_card(row: pd.Series) -> None:
    title = _row_val(row, "title", "Unknown title")
    transition = _row_val(row, "transition", "")
    y_true = _row_val(row, "y_true")
    y_base = _row_val(row, "y_pred_baseline")
    y_cred = _row_val(row, "y_pred_credits")

    badges = (
        class_badge(y_true)
        + class_badge(y_base, kind="status")
        + f' <span class="badge badge-ok">{transition.replace("_", " ")}</span>'
    )

    conf = row.get("confidence")
    delta = row.get("delta_p_true")
    budget = row.get("budget") if "budget" in row.index else None

    prob_lines = []
    for label, bkey, ckey in [
        ("Flop", "base_p_flop", "p_flop"),
        ("Average", "base_p_average", "p_average"),
        ("Hit", "base_p_hit", "p_hit"),
    ]:
        b = format_probability(row[bkey]) if bkey in row.index else "—"
        c = format_probability(row[ckey]) if ckey in row.index else "—"
        prob_lines.append(f"<strong>{label}:</strong> baseline {b} → credits {c}")

    interp = transition_interpretation(transition)
    st.markdown(
        f"""
        <div class="case-card">
            <div class="case-title">{title}</div>
            <div>{badges}</div>
            <div class="case-meta" style="margin-top:0.55rem;">
                <strong>Actual:</strong> {y_true} &nbsp;|&nbsp;
                <strong>Baseline prediction:</strong> {y_base} &nbsp;|&nbsp;
                <strong>Credits prediction:</strong> {y_cred}<br/>
                <strong>Credits confidence:</strong> {format_probability(conf)} &nbsp;|&nbsp;
                <strong>Probability gain on true class:</strong> {format_probability(delta) if delta is not None and not (isinstance(delta, float) and pd.isna(delta)) else format_num(delta, 3)}
            </div>
            <div class="case-meta" style="margin-top:0.45rem;">
                {"<br/>".join(prob_lines)}
            </div>
            <div class="case-meta" style="margin-top:0.55rem;">
                <strong>Genre:</strong> {_row_val(row, "main_genre")} &nbsp;|&nbsp;
                <strong>Budget:</strong> {format_money_millions(budget) if budget is not None and not pd.isna(budget) else _row_val(row, "budget_bucket")} ({_row_val(row, "budget_bucket")})<br/>
                <strong>Runtime:</strong> {_row_val(row, "runtime")} min ({_row_val(row, "runtime_bucket")}) &nbsp;|&nbsp;
                <strong>Scale:</strong> {_row_val(row, "production_scale")} &nbsp;|&nbsp;
                <strong>Talent score:</strong> {format_num(row.get("talent_score"), 2) if "talent_score" in row.index else "—"}<br/>
                <strong>Cast / crew:</strong> {_row_val(row, "cast_size")} / {_row_val(row, "crew_size")} &nbsp;|&nbsp;
                <strong>Known actors:</strong> {_row_val(row, "known_actor_count")} &nbsp;|&nbsp;
                <strong>Franchise flag:</strong> {_row_val(row, "possible_franchise_flag")}<br/>
                <strong>Director:</strong> {_row_val(row, "director_name")}
            </div>
            <div class="case-meta" style="margin-top:0.45rem;font-style:italic;">{interp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_product_sidebar_footer() -> None:
    st.sidebar.caption(
        "Powered by a credits-enriched Logistic Regression model on pre-release TMDB features. "
        "See methodology deck for technical details."
    )


def render_demo_path_expander() -> None:
    with st.expander("Suggested client demo (3 min)"):
        st.markdown(
            """
            1. **Movie Review Queue** — triage real titles  
            2. **Package Simulator** — test a hypothetical release  
            3. **Decision Guidance** — how to use the product responsibly
            """
        )


PRODUCT_QUEUE_COPY = {
    "credits_rescue": (
        "Credits and talent signals corrected the baseline prediction. "
        "This title should be reviewed as a package-sensitive opportunity."
    ),
    "high_confidence_failure": (
        "The model was confident but wrong. This title should enter a human review queue."
    ),
    "strong_correct": (
        "The enriched model aligned with the observed outcome and showed high confidence."
    ),
}


def product_queue_card(row: pd.Series, interpretation: str) -> None:
    """Client-facing review card (compact)."""
    title = _row_val(row, "title", "Unknown title")
    y_true = _row_val(row, "y_true")
    y_base = _row_val(row, "y_pred_baseline")
    y_cred = _row_val(row, "y_pred_credits")
    conf = row.get("confidence")
    transition = _row_val(row, "transition", "")
    badges = class_badge(y_true) + class_badge(y_cred, kind="status")
    st.markdown(
        f"""
        <div class="case-card">
            <div class="case-title">{title}</div>
            <div>{badges}</div>
            <div class="case-meta" style="margin-top:0.45rem;">
                <strong>Actual:</strong> {y_true} &nbsp;|&nbsp;
                <strong>Baseline → Credits:</strong> {y_base} → {y_cred} &nbsp;|&nbsp;
                <strong>Confidence:</strong> {format_probability(conf)}<br/>
                <strong>Genre:</strong> {_row_val(row, "main_genre")} &nbsp;|&nbsp;
                <strong>Budget:</strong> {_row_val(row, "budget_bucket")} &nbsp;|&nbsp;
                <strong>Runtime:</strong> {_row_val(row, "runtime_bucket")} &nbsp;|&nbsp;
                <strong>Scale:</strong> {_row_val(row, "production_scale")}<br/>
                <strong>Talent score:</strong> {format_num(row.get("talent_score"), 2) if "talent_score" in row.index else "—"} &nbsp;|&nbsp;
                <strong>Cast:</strong> {_row_val(row, "cast_size")} &nbsp;|&nbsp;
                <strong>Franchise:</strong> {_row_val(row, "possible_franchise_flag")}
            </div>
            <div class="case-meta" style="margin-top:0.4rem;font-style:italic;">{interpretation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, subtitle: str | None = None) -> None:
    sub_block = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            {sub_block}
        </div>
        """,
        unsafe_allow_html=True,
    )


def model_card(title: str, name: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="model-card">
            <div class="title">{title}</div>
            <div class="name">{name}</div>
            <div class="desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def hero_section(title: str, subtitle: str, paragraph: str) -> None:
    st.markdown(
        f"""
        <div class="hero-box">
            <h1>{title}</h1>
            <p><strong>{subtitle}</strong></p>
            <p>{paragraph}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def use_case_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="use-case-card">
            <h4>{title}</h4>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(title: str, body: str, box_type: Literal["info", "warn", "success"] = "info") -> None:
    css = {"info": "insight-info", "warn": "insight-warn", "success": "insight-success"}[box_type]
    st.markdown(
        f"""
        <div class="{css}">
            <div class="insight-title">{title}</div>
            <div class="insight-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_box(label: str, body: str, level: Literal["low", "medium", "high"] = "medium") -> None:
    st.markdown(
        f"""
        <div class="risk-{level}">
            <strong>{label}</strong><br/>
            <span style="color:#4a5568;font-size:0.92rem;">{body}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_divider() -> None:
    st.markdown("---")


def section_title(text: str) -> None:
    st.markdown(f'<p class="section-title">{text}</p>', unsafe_allow_html=True)


def class_badge(label: str, kind: str = "class") -> str:
    key = str(label).lower().strip()
    if kind == "status":
        css = {"ok": "badge-ok", "rescue": "badge-rescue", "risk": "badge-risk"}.get(key, "badge-ok")
    else:
        css = {"hit": "badge-hit", "average": "badge-average", "flop": "badge-flop"}.get(key, "badge-average")
    return f'<span class="badge {css}">{label.upper()}</span>'


def kpi_card(label: str, value: str, help_text: str | None = None) -> None:
    metric_card(label, value, subtitle=help_text)


def risk_callout(risk_level: str) -> None:
    if "Low confidence" in risk_level:
        risk_box("Risk level", risk_level, "low")
    elif "Higher confidence" in risk_level:
        risk_box("Risk level", risk_level, "high")
    else:
        risk_box("Risk level", risk_level, "medium")


def business_box(text: str) -> None:
    insight_box("Business insight", text, "info")


def show_dataframe(df: pd.DataFrame, **kwargs: Any) -> None:
    params = inspect.signature(st.dataframe).parameters
    opts = dict(kwargs)
    if "hide_index" in params and "hide_index" not in opts:
        opts["hide_index"] = True
    if "use_container_width" in params:
        opts.setdefault("use_container_width", True)
    elif "use_column_width" in params:
        opts["use_column_width"] = True
    st.dataframe(df, **opts)


REGIME_RENAME = {
    "regime": "Regime",
    "accuracy": "Accuracy",
    "macro_f1": "Macro-F1",
    "weighted_f1": "Weighted F1",
    "f1_flop": "F1 flop",
    "f1_average": "F1 average",
    "f1_hit": "F1 hit",
    "model": "Model",
    "model_name": "Model name",
}


def format_metrics_table(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    pct_cols = {"accuracy", "macro_f1", "weighted_f1", "f1_flop", "f1_average", "f1_hit"}
    for col in out.columns:
        if col in pct_cols:
            out[col] = out[col].map(lambda x: format_pct(x) if pd.notna(x) else "—")
    out = out.rename(columns={k: v for k, v in REGIME_RENAME.items() if k in out.columns})
    drop = [c for c in out.columns if c.lower() in ("model_path", "model_key")]
    return out.drop(columns=drop, errors="ignore")


def case_study_card(row: pd.Series, interpretation: str, badge_kind: str) -> None:
    title = row.get("title", "Unknown title")
    y_true = row.get("y_true", "—")
    y_base = row.get("y_pred_baseline", "—")
    y_cred = row.get("y_pred_credits", "—")
    conf = row.get("confidence", None)
    conf_s = format_pct(conf) if conf is not None and pd.notna(conf) else "—"
    transition = row.get("transition", "—")
    genre = row.get("main_genre", "—")
    budget_b = row.get("budget_bucket", "—")
    scale = row.get("production_scale", "—")
    talent = row.get("talent_score", "—")
    if pd.notna(talent):
        talent = f"{float(talent):.2f}"
    cast = row.get("cast_size", "—")
    franch = row.get("possible_franchise_flag", "—")

    badges = (
        class_badge(str(y_true))
        + class_badge(str(badge_kind), kind="status")
        + f' <span class="badge badge-ok">{str(transition).replace("_", " ")}</span>'
    )
    st.markdown(
        f"""
        <div class="case-card">
            <div class="case-title">{title}</div>
            <div>{badges}</div>
            <div class="case-meta" style="margin-top:0.5rem;">
                <strong>Actual:</strong> {y_true} &nbsp;|&nbsp;
                <strong>Baseline → Credits:</strong> {y_base} → {y_cred} &nbsp;|&nbsp;
                <strong>Confidence:</strong> {conf_s}<br/>
                <strong>Genre:</strong> {genre} &nbsp;|&nbsp;
                <strong>Budget:</strong> {budget_b} &nbsp;|&nbsp;
                <strong>Scale:</strong> {scale} &nbsp;|&nbsp;
                <strong>Talent score:</strong> {talent} &nbsp;|&nbsp;
                <strong>Cast size:</strong> {cast} &nbsp;|&nbsp;
                <strong>Franchise flag:</strong> {franch}
            </div>
            <div class="case-meta" style="margin-top:0.45rem;font-style:italic;">{interpretation}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


SIMULATOR_PRESETS: dict[str, dict[str, Any]] = {
    "Indie drama": {
        "budget": 8_000_000,
        "runtime": 105,
        "main_genre": "Drama",
        "original_language": "en",
        "release_month": 10,
        "release_quarter": 4,
        "genre_count": 1,
        "production_company_count": 1,
        "production_country_count": 1,
        "spoken_language_count": 1,
        "cast_size": 12,
        "crew_size": 15,
        "writer_count": 2,
        "director_name": "__missing__",
        "known_actor_count": 1,
        "top_billed_cast_count": 3,
        "possible_franchise_flag": 0,
        "ensemble_cast_flag": 0,
        "top_director_flag": 0,
    },
    "Franchise action movie": {
        "budget": 150_000_000,
        "runtime": 128,
        "main_genre": "Action",
        "original_language": "en",
        "release_month": 7,
        "release_quarter": 3,
        "genre_count": 2,
        "production_company_count": 4,
        "production_country_count": 2,
        "spoken_language_count": 1,
        "cast_size": 45,
        "crew_size": 80,
        "writer_count": 4,
        "director_name": "__missing__",
        "known_actor_count": 6,
        "top_billed_cast_count": 8,
        "possible_franchise_flag": 1,
        "ensemble_cast_flag": 1,
        "top_director_flag": 1,
    },
    "Low-budget horror": {
        "budget": 5_000_000,
        "runtime": 92,
        "main_genre": "Horror",
        "original_language": "en",
        "release_month": 10,
        "release_quarter": 4,
        "genre_count": 1,
        "production_company_count": 1,
        "production_country_count": 1,
        "spoken_language_count": 1,
        "cast_size": 10,
        "crew_size": 18,
        "writer_count": 2,
        "director_name": "__missing__",
        "known_actor_count": 0,
        "top_billed_cast_count": 2,
        "possible_franchise_flag": 0,
        "ensemble_cast_flag": 0,
        "top_director_flag": 0,
    },
    "Animation family movie": {
        "budget": 90_000_000,
        "runtime": 95,
        "main_genre": "Animation",
        "original_language": "en",
        "release_month": 6,
        "release_quarter": 2,
        "genre_count": 2,
        "production_company_count": 2,
        "production_country_count": 1,
        "spoken_language_count": 2,
        "cast_size": 20,
        "crew_size": 55,
        "writer_count": 5,
        "director_name": "__missing__",
        "known_actor_count": 3,
        "top_billed_cast_count": 5,
        "possible_franchise_flag": 1,
        "ensemble_cast_flag": 0,
        "top_director_flag": 0,
    },
    "High-budget ensemble cast": {
        "budget": 200_000_000,
        "runtime": 138,
        "main_genre": "Adventure",
        "original_language": "en",
        "release_month": 5,
        "release_quarter": 2,
        "genre_count": 3,
        "production_company_count": 5,
        "production_country_count": 3,
        "spoken_language_count": 2,
        "cast_size": 60,
        "crew_size": 120,
        "writer_count": 6,
        "director_name": "__missing__",
        "known_actor_count": 8,
        "top_billed_cast_count": 10,
        "possible_franchise_flag": 1,
        "ensemble_cast_flag": 1,
        "top_director_flag": 1,
    },
}


def profile_drivers(user_inputs: dict[str, Any]) -> list[str]:
    drivers: list[str] = []
    budget = float(user_inputs.get("budget", 0) or 0)
    if budget >= 100_000_000:
        drivers.append("Large production budget signals studio-scale release.")
    elif budget <= 15_000_000:
        drivers.append("Modest budget profile consistent with indie / mid-scale risk.")

    cast = int(user_inputs.get("cast_size", 0) or 0)
    if cast >= 40:
        drivers.append("Large cast footprint — ensemble packaging may shift talent signal.")
    elif cast <= 15:
        drivers.append("Compact cast — packaging signal driven by a smaller billed ensemble.")

    if int(user_inputs.get("possible_franchise_flag", 0) or 0) == 1:
        drivers.append("Franchise / sequel heuristic flagged — IP continuity may lift hit probability.")

    if int(user_inputs.get("top_director_flag", 0) or 0) == 1:
        drivers.append("Top director flag — experienced director in training cohort.")
    elif user_inputs.get("director_name", "__missing__") not in ("__missing__", "", None):
        drivers.append("Named director — mapped to historical training frequency where known.")

    ka = int(user_inputs.get("known_actor_count", 0) or 0)
    if ka >= 4:
        drivers.append("Several known actors in top billing — stronger talent density.")
    elif ka == 0:
        drivers.append("Limited known-actor footprint in top billing.")

    pcc = int(user_inputs.get("production_company_count", 0) or 0)
    if pcc >= 4:
        drivers.append("Multi-company production — larger ecosystem / scale proxy.")

    if int(user_inputs.get("ensemble_cast_flag", 0) or 0) == 1:
        drivers.append("Ensemble cast flag — broad on-screen talent spread.")

    if not drivers:
        drivers.append("Profile is mid-range on budget and talent proxies — review probabilities carefully.")
    return drivers


def artifacts_ready() -> bool:
    model_path = MODELS["credits_logistic_regression"]["path"]
    return model_path.exists() and TRAIN_ARTIFACTS_FILE.exists()


def show_missing_artifacts_warning() -> None:
    st.warning(
        "Model artifacts are missing. Run the training script from the project root:\n\n"
        "```bash\npython scripts/train_models.py\n```"
    )


@st.cache_resource(show_spinner=False)
def get_champion_bundle():
    if not artifacts_ready():
        return None
    from inference import load_champion_bundle

    return load_champion_bundle()


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.caption(subtitle)
