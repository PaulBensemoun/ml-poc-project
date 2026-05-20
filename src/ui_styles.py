"""UI styling and i18n strings for the Movie Success Predictor app.

Centralizes CSS and bilingual (FR/EN) strings used by the Streamlit pages.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


LANG_DEFAULT = "fr"
LANGUAGES = {"fr": "Français", "en": "English"}


def get_lang() -> str:
    return st.session_state.get("lang", LANG_DEFAULT)


def set_lang(lang: str) -> None:
    st.session_state["lang"] = lang if lang in LANGUAGES else LANG_DEFAULT


def t(key: str, **fmt: Any) -> str:
    lang = get_lang()
    val = TRANSLATIONS.get(key, {}).get(lang) or TRANSLATIONS.get(key, {}).get("en") or key
    if fmt:
        try:
            return val.format(**fmt)
        except (KeyError, IndexError, ValueError):
            return val
    return val


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


# Brand palette
PALETTE = {
    "primary": "#1E3A8A",       # navy — brand
    "primary_dark": "#0F172A",
    "accent": "#2563EB",        # blue — primary CTAs
    "accent_soft": "#DBEAFE",
    "secondary": "#F59E0B",     # amber — secondary CTAs, highlights
    "secondary_soft": "#FEF3C7",
    "success": "#15803D",
    "success_soft": "#DCFCE7",
    "warning": "#B45309",
    "warning_soft": "#FEF3C7",
    "danger": "#B91C1C",
    "danger_soft": "#FEE2E2",
    "neutral_bg": "#F8FAFC",
    "card_bg": "#FFFFFF",
    "border": "#E2E8F0",
    "text": "#0F172A",
    "muted": "#475569",
    "muted_soft": "#94A3B8",
}

CLASS_COLORS = {
    "hit": "#15803D",
    "average": "#F59E0B",
    "flop": "#B91C1C",
}

CLASS_COLORS_PLOTLY = {
    "hit": "#22C55E",
    "average": "#F59E0B",
    "flop": "#EF4444",
}

# Inline SVG logo (used in sidebar header and PDF cover)
LOGO_SVG = (
    '<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0%" stop-color="#2563EB"/><stop offset="100%" stop-color="#1E3A8A"/>'
    '</linearGradient></defs>'
    '<rect x="2" y="2" width="36" height="36" rx="9" fill="url(#g)"/>'
    '<circle cx="13" cy="13" r="2" fill="white" opacity="0.95"/>'
    '<circle cx="20" cy="11" r="2" fill="white" opacity="0.85"/>'
    '<circle cx="27" cy="13" r="2" fill="white" opacity="0.75"/>'
    '<path d="M10 22 L20 28 L30 22 L20 16 Z" fill="white" opacity="0.95"/>'
    '<path d="M20 28 L20 34" stroke="white" stroke-width="2" stroke-linecap="round"/>'
    '</svg>'
)

# Icons used as visual hints in inputs
ICONS = {
    "budget": "💵",
    "runtime": "⏱️",
    "genre": "🎭",
    "language": "🌐",
    "release": "📅",
    "production": "🏢",
    "cast": "👥",
    "crew": "🎬",
    "writers": "✍️",
    "director": "🎯",
    "franchise": "🔁",
    "ensemble": "🧑‍🤝‍🧑",
    "top": "⭐",
    "hit": "🚀",
    "flop": "⚠️",
    "average": "➖",
}


_CSS = """
<style>
:root {
    --brand-primary: #1E3A8A;
    --brand-accent: #2563EB;
    --brand-soft: #DBEAFE;
    --brand-success: #15803D;
    --brand-warning: #B45309;
    --brand-danger: #B91C1C;
    --neutral-bg: #F8FAFC;
    --card-bg: #FFFFFF;
    --border: #E2E8F0;
    --text: #0F172A;
    --muted: #475569;
    --muted-soft: #94A3B8;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
    color: var(--text);
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1300px;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
}
section[data-testid="stSidebar"] * {
    color: #E2E8F0 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #E2E8F0 !important;
    font-weight: 500;
}
section[data-testid="stSidebar"] hr {
    border-color: #334155;
}

/* Brand header */
.brand-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0 1rem 0;
    border-bottom: 1px solid #334155;
    margin-bottom: 1rem;
}
.brand-logo {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg, #2563EB, #1E3A8A);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.2rem;
    font-weight: 700;
}
.brand-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #F8FAFC !important;
    margin: 0;
    line-height: 1.2;
}
.brand-tag {
    font-size: 0.72rem;
    color: #94A3B8 !important;
    margin: 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
    color: white;
    border-radius: 16px;
    padding: 2.2rem 2.4rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 14px rgba(30, 58, 138, 0.18);
}
.hero h1 {
    color: white;
    margin: 0 0 0.5rem 0;
    font-size: 1.95rem;
    font-weight: 700;
}
.hero p {
    color: rgba(255, 255, 255, 0.92);
    margin: 0;
    font-size: 1.02rem;
    max-width: 780px;
    line-height: 1.55;
}
.hero .hero-meta {
    margin-top: 1rem;
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    color: rgba(255,255,255,0.85);
    font-size: 0.85rem;
}

/* Cards */
.card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    height: 100%;
}
.card-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin: 0 0 0.5rem 0;
    font-weight: 600;
}
.card-value {
    font-size: 1.7rem;
    font-weight: 700;
    color: var(--text);
    margin: 0;
    line-height: 1.15;
}
.card-sub {
    font-size: 0.85rem;
    color: var(--muted);
    margin-top: 0.45rem;
    line-height: 1.45;
}
.card-accent {
    border-left: 4px solid var(--brand-accent);
}
.card-success {
    border-left: 4px solid var(--brand-success);
}
.card-warning {
    border-left: 4px solid var(--brand-warning);
}
.card-danger {
    border-left: 4px solid var(--brand-danger);
}

/* Outcome badge */
.outcome {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.02em;
}
.outcome-hit { background: #DCFCE7; color: #15803D; }
.outcome-average { background: #FEF3C7; color: #92400E; }
.outcome-flop { background: #FEE2E2; color: #B91C1C; }

.dot {
    display: inline-block;
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
}

/* Probability bar */
.probability-row {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    margin: 0.45rem 0;
}
.probability-row .label {
    flex: 0 0 110px;
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text);
}
.probability-row .value {
    flex: 0 0 56px;
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: 600;
    color: var(--text);
}
.probability-row .track {
    flex: 1 1 auto;
    height: 12px;
    border-radius: 999px;
    background: #F1F5F9;
    overflow: hidden;
    position: relative;
}
.probability-row .fill {
    height: 100%;
    border-radius: 999px;
}
.fill-hit { background: linear-gradient(90deg, #22C55E, #15803D); }
.fill-average { background: linear-gradient(90deg, #FBBF24, #B45309); }
.fill-flop { background: linear-gradient(90deg, #F87171, #B91C1C); }

/* Driver pills */
.driver-pill {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    background: var(--brand-soft);
    color: var(--brand-primary);
    font-size: 0.85rem;
    margin: 0.2rem 0.3rem 0.2rem 0;
    font-weight: 500;
}
.driver-up { background: #DCFCE7; color: #15803D; }
.driver-down { background: #FEE2E2; color: #B91C1C; }
.driver-neutral { background: #E2E8F0; color: #334155; }

/* Section heading */
.section-title {
    font-size: 1.18rem;
    font-weight: 700;
    color: var(--brand-primary);
    margin: 1.6rem 0 0.75rem 0;
    border-bottom: 2px solid var(--brand-soft);
    padding-bottom: 0.4rem;
}

/* Insight box */
.insight {
    background: var(--neutral-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.15rem;
    margin: 0.65rem 0;
}
.insight-warn {
    background: #FFFBEB;
    border-color: #FCD34D;
}
.insight-success {
    background: #F0FDF4;
    border-color: #86EFAC;
}
.insight-title {
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
    font-size: 0.95rem;
}
.insight-body {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.5;
}

/* Comparable card */
.comp-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    height: 100%;
}
.comp-title {
    font-weight: 700;
    font-size: 0.98rem;
    color: var(--text);
    margin-bottom: 0.25rem;
}
.comp-meta {
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.45;
}
.comp-similarity {
    display: inline-block;
    background: var(--brand-soft);
    color: var(--brand-primary);
    font-size: 0.78rem;
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    font-weight: 600;
    margin-top: 0.4rem;
}

/* Sensitivity table */
.sens-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.55rem 0.85rem;
    border-bottom: 1px solid var(--border);
    font-size: 0.92rem;
}
.sens-row:last-child { border-bottom: none; }
.sens-label { font-weight: 600; color: var(--text); }
.sens-delta-up { color: var(--brand-success); font-weight: 700; }
.sens-delta-down { color: var(--brand-danger); font-weight: 700; }
.sens-delta-flat { color: var(--muted); }

/* Compact metric row */
.kpi-row { display: flex; gap: 1rem; flex-wrap: wrap; }
.kpi-pill {
    background: var(--neutral-bg);
    border: 1px solid var(--border);
    padding: 0.6rem 0.9rem;
    border-radius: 8px;
    font-size: 0.88rem;
}
.kpi-pill strong { color: var(--brand-primary); }

/* Step indicator (wizard) */
.steps {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.step {
    flex: 1;
    text-align: center;
    padding: 0.55rem 0.5rem;
    border-radius: 8px;
    background: var(--neutral-bg);
    border: 1px solid var(--border);
    font-size: 0.85rem;
    color: var(--muted);
    font-weight: 600;
}
.step.active {
    background: var(--brand-primary);
    color: white;
    border-color: var(--brand-primary);
}
.step.done {
    background: var(--brand-soft);
    color: var(--brand-primary);
    border-color: var(--brand-soft);
}

/* Buttons */
.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    border: 1px solid var(--border);
    transition: all 0.15s ease;
}
.stButton > button[kind="primary"] {
    background: var(--brand-primary);
    border-color: var(--brand-primary);
}
.stButton > button[kind="primary"]:hover {
    background: var(--brand-accent);
    border-color: var(--brand-accent);
}
.stButton > button[kind="secondary"] {
    background: var(--brand-secondary);
    border-color: var(--brand-secondary);
    color: white;
}
.stButton > button[kind="secondary"]:hover {
    filter: brightness(1.08);
}

/* Demo case cards (Dashboard) */
.demo-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.25rem;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
    height: 100%;
    display: flex;
    flex-direction: column;
    transition: all 0.18s ease;
}
.demo-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(37, 99, 235, 0.13);
    border-color: var(--brand-accent);
}
.demo-card .demo-emoji {
    font-size: 1.85rem;
    margin-bottom: 0.4rem;
}
.demo-card .demo-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    margin: 0.1rem 0 0.4rem 0;
}
.demo-card .demo-desc {
    font-size: 0.86rem;
    color: var(--muted);
    line-height: 1.45;
    flex: 1;
    margin-bottom: 0.75rem;
}
.demo-card .demo-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
    margin-bottom: 0.6rem;
}
.demo-card .demo-tag {
    background: var(--neutral-bg);
    color: var(--muted);
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 500;
}

/* Hero CTAs row */
.hero-cta-row {
    display: flex;
    gap: 0.7rem;
    margin-top: 1.2rem;
    flex-wrap: wrap;
}
.hero-stat-row {
    display: flex;
    gap: 1.8rem;
    margin-top: 1.4rem;
    flex-wrap: wrap;
}
.hero-stat {
    color: rgba(255,255,255,0.95);
    border-left: 3px solid rgba(255,255,255,0.4);
    padding-left: 0.75rem;
}
.hero-stat .v {
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.1;
}
.hero-stat .l {
    font-size: 0.75rem;
    opacity: 0.85;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* Onboarding banner */
.onboarding {
    background: linear-gradient(135deg, #FEF3C7 0%, #FED7AA 100%);
    border: 1px solid #F59E0B;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin: 0 0 1rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
}
.onboarding-text {
    color: #92400E;
    font-size: 0.92rem;
    line-height: 1.5;
}
.onboarding-text strong { color: #78350F; }

/* Stat strip */
.stat-strip {
    display: flex;
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}
.stat-strip-item {
    flex: 1;
    padding: 0.85rem 1.1rem;
    border-right: 1px solid var(--border);
    text-align: center;
}
.stat-strip-item:last-child { border-right: none; }
.stat-strip-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
    margin-bottom: 0.25rem;
}
.stat-strip-value {
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text);
}

/* Result hero */
.result-hero {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.6rem 1.8rem;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
    margin-bottom: 1.2rem;
}
.score-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    color: var(--muted);
    letter-spacing: 0.05em;
}
.score-value {
    font-size: 3.2rem;
    font-weight: 800;
    line-height: 1;
    color: var(--brand-primary);
    font-variant-numeric: tabular-nums;
}
.score-suffix {
    font-size: 1.2rem;
    color: var(--muted-soft);
    font-weight: 600;
}

/* Comparison column header */
.compare-col-header {
    background: linear-gradient(135deg, var(--brand-primary), var(--brand-accent));
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 10px 10px 0 0;
    font-weight: 700;
    text-align: center;
    font-size: 0.95rem;
}
.compare-col-header.winner {
    background: linear-gradient(135deg, #15803D, #22C55E);
}

/* Compare summary card */
.compare-result {
    background: white;
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 0 0 10px 10px;
    padding: 1rem 1.1rem;
}
.compare-result .name {
    font-weight: 700;
    color: var(--text);
    font-size: 1.05rem;
    margin-bottom: 0.45rem;
}

/* Plotly container clean */
[data-testid="stPlotlyChart"] > div {
    border-radius: 10px;
}
</style>
"""


# --- i18n dictionary -----------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {
    # Branding
    "brand_name": {"fr": "CinéSignal", "en": "CinéSignal"},
    "brand_tag": {"fr": "Movie Success Intelligence", "en": "Movie Success Intelligence"},

    # Navigation
    "nav_dashboard": {"fr": "Accueil", "en": "Dashboard"},
    "nav_predict": {"fr": "Prédire", "en": "Predict"},
    "nav_compare": {"fr": "Comparer", "en": "Compare"},
    "nav_insights": {"fr": "Benchmarks", "en": "Insights"},
    "nav_label": {"fr": "Navigation", "en": "Navigation"},
    "lang_label": {"fr": "Langue", "en": "Language"},
    "sidebar_status_ready": {"fr": "Modèle prêt", "en": "Model ready"},
    "sidebar_status_missing": {"fr": "Modèle manquant — lancer `python scripts/train_models.py`", "en": "Model missing — run `python scripts/train_models.py`"},
    "sidebar_footer": {
        "fr": "Modèle : régression logistique enrichie crédits (TMDB + cast & crew).",
        "en": "Model: credits-enriched logistic regression (TMDB + cast & crew).",
    },
    "deck_link": {"fr": "Voir le deck méthodologique", "en": "View methodology deck"},

    # Dashboard
    "hero_title": {
        "fr": "Anticipez le succès commercial d'un film avant sa sortie",
        "en": "Anticipate a movie's commercial success before release",
    },
    "hero_body": {
        "fr": "Outil d'aide à la décision pour studios, producteurs et investisseurs. "
              "Saisissez le profil d'un projet et obtenez une estimation interprétable "
              "des chances qu'il soit un flop, un film moyen ou un hit.",
        "en": "Decision-support tool for studios, producers and investors. "
              "Describe a project's profile and get an interpretable estimate of its "
              "probability of being a flop, average movie, or hit.",
    },
    "hero_cta": {
        "fr": "Commencer une prédiction",
        "en": "Start a prediction",
    },
    "dashboard_kpi_title": {"fr": "Performance du modèle", "en": "Model performance"},
    "dashboard_value_title": {"fr": "Comment utiliser cet outil", "en": "How to use this tool"},
    "kpi_movies": {"fr": "Films analysés", "en": "Movies analyzed"},
    "kpi_test": {"fr": "Films de test", "en": "Test movies"},
    "kpi_accuracy": {"fr": "Précision globale", "en": "Accuracy"},
    "kpi_macro_f1": {"fr": "Macro-F1", "en": "Macro-F1"},
    "kpi_f1_hit": {"fr": "F1 Hit", "en": "F1 Hit"},
    "kpi_f1_flop": {"fr": "F1 Flop", "en": "F1 Flop"},
    "use_case_portfolio_title": {"fr": "Triage de portefeuille", "en": "Portfolio triage"},
    "use_case_portfolio_body": {
        "fr": "Évaluez rapidement plusieurs projets en développement pour prioriser ceux qui méritent une revue analyste approfondie.",
        "en": "Quickly assess multiple projects in development to prioritize those that deserve deeper analyst review.",
    },
    "use_case_packaging_title": {"fr": "Évaluation de packaging", "en": "Packaging evaluation"},
    "use_case_packaging_body": {
        "fr": "Testez différentes configurations de cast, réalisateur et budget pour voir comment le profil de risque évolue.",
        "en": "Test different cast, director, and budget configurations to see how the risk profile shifts.",
    },
    "use_case_risk_title": {"fr": "Revue de risque", "en": "Risk review"},
    "use_case_risk_body": {
        "fr": "Identifiez les projets à faible confiance ou à profil atypique pour les remonter à un comité de décision.",
        "en": "Identify low-confidence or atypical projects and escalate them to a decision committee.",
    },
    "dashboard_disclaimer_title": {"fr": "Utilisation responsable", "en": "Responsible use"},
    "dashboard_disclaimer_body": {
        "fr": "Cet outil est un support à la décision, pas un moteur de greenlight automatique. "
              "Les prédictions doivent toujours être combinées avec une analyse de marché, "
              "une revue éditoriale et le jugement d'experts.",
        "en": "This tool is decision support, not an automatic greenlight engine. "
              "Predictions should always be combined with market analysis, editorial review, "
              "and expert judgment.",
    },

    # Predict page — wizard
    "predict_title": {"fr": "Prédire le succès commercial", "en": "Predict commercial success"},
    "predict_subtitle": {
        "fr": "Décrivez votre projet en 3 étapes pour obtenir une estimation interprétable.",
        "en": "Describe your project in 3 steps to get an interpretable estimate.",
    },
    "step_1": {"fr": "1. Projet", "en": "1. Project"},
    "step_2": {"fr": "2. Production", "en": "2. Production"},
    "step_3": {"fr": "3. Talents & packaging", "en": "3. Talent & packaging"},
    "preset_label": {"fr": "Modèle de projet", "en": "Project template"},
    "preset_custom": {"fr": "Personnalisé", "en": "Custom"},
    "preset_indie_drama": {"fr": "Drame indépendant", "en": "Indie drama"},
    "preset_franchise_action": {"fr": "Blockbuster franchise", "en": "Franchise blockbuster"},
    "preset_low_budget_horror": {"fr": "Horreur petit budget", "en": "Low-budget horror"},
    "preset_animation_family": {"fr": "Animation familiale", "en": "Family animation"},
    "preset_ensemble": {"fr": "Cast ensemble premium", "en": "Premium ensemble cast"},
    "preset_romcom": {"fr": "Comédie romantique", "en": "Romantic comedy"},
    "field_budget": {"fr": "Budget (USD)", "en": "Budget (USD)"},
    "field_runtime": {"fr": "Durée (minutes)", "en": "Runtime (minutes)"},
    "field_genre": {"fr": "Genre principal", "en": "Main genre"},
    "field_language": {"fr": "Langue originale", "en": "Original language"},
    "field_release_month": {"fr": "Mois de sortie", "en": "Release month"},
    "field_release_quarter": {"fr": "Trimestre de sortie", "en": "Release quarter"},
    "field_genre_count": {"fr": "Nombre de genres", "en": "Genre count"},
    "field_prod_companies": {"fr": "Sociétés de production", "en": "Production companies"},
    "field_prod_countries": {"fr": "Pays de production", "en": "Production countries"},
    "field_spoken_languages": {"fr": "Langues parlées", "en": "Spoken languages"},
    "field_cast_size": {"fr": "Taille du casting", "en": "Cast size"},
    "field_crew_size": {"fr": "Taille de l'équipe", "en": "Crew size"},
    "field_writer_count": {"fr": "Nombre de scénaristes", "en": "Writers"},
    "field_known_actors": {"fr": "Acteurs reconnus dans le top billing", "en": "Known actors in top billing"},
    "field_top_billed": {"fr": "Têtes d'affiche", "en": "Top-billed cast"},
    "field_franchise": {"fr": "Suite / franchise ?", "en": "Sequel / franchise?"},
    "field_ensemble": {"fr": "Cast ensemble ?", "en": "Ensemble cast?"},
    "field_top_director": {"fr": "Réalisateur reconnu ?", "en": "Top director?"},
    "field_director": {"fr": "Réalisateur", "en": "Director"},
    "field_director_unknown": {"fr": "Inconnu / non renseigné", "en": "Unknown / not specified"},
    "field_director_custom": {"fr": "Saisir un nom…", "en": "Type a name…"},
    "yes": {"fr": "Oui", "en": "Yes"},
    "no": {"fr": "Non", "en": "No"},
    "btn_back": {"fr": "Précédent", "en": "Back"},
    "btn_next": {"fr": "Suivant", "en": "Next"},
    "btn_predict": {"fr": "Lancer la prédiction", "en": "Run prediction"},
    "btn_reset": {"fr": "Réinitialiser", "en": "Reset"},

    # Predict — results
    "result_title": {"fr": "Résultat de la prédiction", "en": "Prediction result"},
    "result_outcome": {"fr": "Issue prédite", "en": "Predicted outcome"},
    "result_confidence": {"fr": "Confiance", "en": "Confidence"},
    "result_risk": {"fr": "Niveau de risque", "en": "Risk level"},
    "result_probabilities": {"fr": "Distribution des probabilités", "en": "Probability distribution"},
    "result_interpretation": {"fr": "Interprétation business", "en": "Business interpretation"},
    "result_drivers_title": {"fr": "Principaux facteurs explicatifs", "en": "Key explanatory drivers"},
    "result_sensitivity_title": {"fr": "Analyse de sensibilité", "en": "Sensitivity analysis"},
    "result_sensitivity_help": {
        "fr": (
            "Comment la probabilité d'être un hit évolue si vous modifiez un seul levier. "
            "Note : un hit est défini par un ROI ≥ 2× — augmenter le budget rend cette barre "
            "plus difficile à atteindre, donc P(hit) peut baisser même si le film devient plus ambitieux."
        ),
        "en": (
            "How P(hit) shifts when you change a single lever. "
            "Note: a hit is defined as ROI ≥ 2× — a larger budget raises the revenue bar, "
            "so P(hit) can decrease even though the project becomes more ambitious."
        ),
    },
    "result_comparables_title": {"fr": "Films historiques comparables", "en": "Comparable historical movies"},
    "result_comparables_help": {
        "fr": "Trois films réels du dataset TMDB ayant le profil le plus proche.",
        "en": "Three real movies from the TMDB dataset with the closest profile.",
    },
    "result_export_title": {"fr": "Exporter le rapport", "en": "Export report"},
    "result_export_pdf": {"fr": "Télécharger le PDF", "en": "Download PDF"},
    "result_export_json": {"fr": "Télécharger JSON", "en": "Download JSON"},
    "outcome_hit": {"fr": "HIT — fort potentiel", "en": "HIT — strong potential"},
    "outcome_average": {"fr": "MOYEN — rentabilité incertaine", "en": "AVERAGE — uncertain profitability"},
    "outcome_flop": {"fr": "FLOP — risque élevé", "en": "FLOP — high risk"},
    "risk_low": {"fr": "Confiance modeste — revue analyste recommandée", "en": "Low confidence — analyst review recommended"},
    "risk_medium": {"fr": "Confiance modérée — à utiliser comme support de discussion", "en": "Moderate confidence — use as discussion input"},
    "risk_high": {"fr": "Confiance plus élevée — toujours valider avec le contexte marché", "en": "Higher confidence — still validate with market context"},
    "biz_hit": {
        "fr": "Le profil saisi présente des signaux compatibles avec un succès commercial. "
              "Le modèle estime que la classe la plus probable est **hit** avec une confiance de {conf}. "
              "Validez avec une analyse marketing et de calendrier de sortie.",
        "en": "The submitted profile shows signals consistent with commercial success. "
              "The model estimates **hit** as the most likely class with {conf} confidence. "
              "Validate with marketing analysis and release schedule.",
    },
    "biz_average": {
        "fr": "Le profil saisi est mitigé. Le modèle penche pour un film **moyen** (confiance {conf}). "
              "C'est la classe la plus difficile à prédire — la revue éditoriale et marketing est cruciale.",
        "en": "The profile is mixed. The model leans towards an **average** outcome (confidence {conf}). "
              "This is the hardest class to predict — editorial and marketing review is critical.",
    },
    "biz_flop": {
        "fr": "Le profil saisi présente plusieurs signaux de risque. Le modèle classe ce projet comme un **flop potentiel** "
              "(confiance {conf}). Considérez un ajustement du budget, du calendrier ou du packaging.",
        "en": "The profile shows multiple risk signals. The model classifies this project as a **potential flop** "
              "(confidence {conf}). Consider adjusting budget, schedule, or packaging.",
    },

    # Drivers
    "driver_budget_high": {"fr": "Budget important — signal de production de grande envergure", "en": "Large budget — signals studio-scale release"},
    "driver_budget_low": {"fr": "Budget modeste — profil indé ou mid-scale", "en": "Modest budget — indie / mid-scale profile"},
    "driver_franchise": {"fr": "Franchise / suite — l'IP existante augmente la probabilité de hit", "en": "Franchise / sequel — existing IP boosts hit probability"},
    "driver_known_actors_many": {"fr": "Plusieurs acteurs reconnus en tête d'affiche", "en": "Multiple known actors in top billing"},
    "driver_known_actors_none": {"fr": "Peu d'acteurs reconnus en tête d'affiche", "en": "Limited known-actor footprint"},
    "driver_top_director": {"fr": "Réalisateur expérimenté du cohort d'entraînement", "en": "Experienced director from the training cohort"},
    "driver_ensemble": {"fr": "Cast ensemble — densité de talents on-screen importante", "en": "Ensemble cast — broad on-screen talent density"},
    "driver_summer": {"fr": "Sortie estivale — créneau blockbuster classique", "en": "Summer release — classic blockbuster window"},
    "driver_holiday": {"fr": "Sortie de fin d'année — fenêtre familiale et prestige", "en": "End-of-year release — family / prestige window"},
    "driver_short": {"fr": "Durée courte — adapté aux comédies / horreur, moins aux blockbusters", "en": "Short runtime — suits comedy / horror, less so blockbusters"},
    "driver_long": {"fr": "Durée longue — typique des epics et drames prestige", "en": "Long runtime — typical for epics and prestige dramas"},
    "driver_multi_company": {"fr": "Production multi-sociétés — proxy d'envergure", "en": "Multi-company production — scale proxy"},
    "driver_default": {"fr": "Profil intermédiaire — examiner les probabilités avec attention", "en": "Mid-range profile — review probabilities carefully"},

    # Sensitivity
    "sens_known_actor_plus": {"fr": "Ajouter 2 acteurs reconnus", "en": "Add 2 known actors"},
    "sens_known_actor_minus": {"fr": "Retirer les acteurs reconnus", "en": "Remove all known actors"},
    "sens_top_director": {"fr": "Engager un réalisateur reconnu", "en": "Hire a top director"},
    "sens_franchise_on": {"fr": "Transformer en franchise / suite", "en": "Turn into franchise / sequel"},
    "sens_budget_up": {"fr": "Augmenter le budget de 50 %", "en": "Increase budget by 50%"},
    "sens_budget_down": {"fr": "Réduire le budget de 50 %", "en": "Reduce budget by 50%"},
    "sens_ensemble": {"fr": "Activer le cast ensemble", "en": "Activate ensemble cast"},

    # Compare page
    "compare_title": {"fr": "Comparer plusieurs scénarios", "en": "Compare multiple scenarios"},
    "compare_subtitle": {
        "fr": "Évaluez côte à côte jusqu'à 4 configurations de projet pour identifier la plus prometteuse.",
        "en": "Evaluate up to 4 project configurations side-by-side to find the most promising one.",
    },
    "compare_add": {"fr": "Ajouter un scénario", "en": "Add a scenario"},
    "compare_remove": {"fr": "Retirer", "en": "Remove"},
    "compare_run": {"fr": "Lancer la comparaison", "en": "Run comparison"},
    "compare_scenario": {"fr": "Scénario {n}", "en": "Scenario {n}"},
    "compare_name": {"fr": "Nom du scénario", "en": "Scenario name"},
    "compare_winner": {"fr": "Meilleur potentiel de hit", "en": "Highest hit potential"},
    "compare_summary": {"fr": "Synthèse comparative", "en": "Comparative summary"},
    "compare_empty": {"fr": "Ajoutez au moins 2 scénarios pour les comparer.", "en": "Add at least 2 scenarios to compare them."},
    "compare_max": {"fr": "Maximum 4 scénarios.", "en": "Maximum 4 scenarios."},

    # Insights page
    "insights_title": {"fr": "Benchmarks & signaux marché", "en": "Benchmarks & market signals"},
    "insights_subtitle": {
        "fr": "Tendances historiques issues du dataset TMDB qui contextualisent les prédictions.",
        "en": "Historical trends from the TMDB dataset that contextualize predictions.",
    },
    "insights_tab_classes": {"fr": "Classes & ROI", "en": "Classes & ROI"},
    "insights_tab_budget": {"fr": "Budget & échelle", "en": "Budget & scale"},
    "insights_tab_genre": {"fr": "Genres", "en": "Genres"},
    "insights_tab_timing": {"fr": "Timing & langue", "en": "Timing & language"},
    "insights_tab_credits": {"fr": "Crédits & talents", "en": "Credits & talent"},

    # Generic
    "common_more": {"fr": "Voir plus", "en": "More"},
    "common_close": {"fr": "Fermer", "en": "Close"},
    "common_loading": {"fr": "Chargement…", "en": "Loading…"},
    "common_no_data": {"fr": "Pas de données disponibles", "en": "No data available"},
    "common_not_available": {"fr": "Non disponible", "en": "Not available"},
    "common_search": {"fr": "Rechercher…", "en": "Search…"},
    "common_continue": {"fr": "Continuer", "en": "Continue"},
    "common_dismiss": {"fr": "Compris", "en": "Got it"},

    # Form helpers extras
    "field_budget_help": {
        "fr": "Faites glisser le curseur : pas de 500 k$ de 0 à 50 M$, puis paliers plus larges jusqu'à 400 M$. "
              "Montants affichés avec séparateurs de milliers.",
        "en": "Drag the slider: $500K steps from $0 to $50M, then wider steps up to $400M. "
              "Amounts shown with thousand separators.",
    },
    "field_director_placeholder": {"fr": "ex: Christopher Nolan", "en": "e.g. Christopher Nolan"},
    "field_director_help": {
        "fr": "Tapez un nom : la liste suggère les réalisateurs connus du modèle.",
        "en": "Type a name: matches are suggested from the model's known directors.",
    },
    "field_top_billed_help": {
        "fr": "Nombre d'acteurs crédités parmi les 5 premières places du casting (ordre d'affiche TMDB). "
              "Ce n'est pas la taille totale du cast.",
        "en": "How many actors are credited in the top 5 billing slots (TMDB order). "
              "Not the same as total cast size.",
    },
    "field_ensemble_help": {
        "fr": "Oui = film à plusieurs rôles importants (ex. Avengers). "
              "Non = histoire centrée sur un ou deux protagonistes (ex. drame intimiste).",
        "en": "Yes = many equally important roles (e.g. ensemble blockbuster). "
              "No = story focused on one or two leads (e.g. intimate drama).",
    },
    "field_director_known": {"fr": "— connu du modèle", "en": "— known to the model"},
    "field_director_suggestions": {"fr": "Suggestions", "en": "Suggestions"},
    "field_director_use_as_custom": {"fr": "(garder tel quel)", "en": "(keep as typed)"},

    # Onboarding / demo cases
    "onboarding_title": {"fr": "Première visite ?", "en": "First visit?"},
    "onboarding_body": {
        "fr": "Essayez un cas de démonstration ou lancez votre propre prédiction. "
              "Tout est interactif — modifiez les paramètres et voyez l'impact en direct.",
        "en": "Try a demo case or run your own prediction. Everything is interactive — "
              "tweak the parameters and see the impact live.",
    },
    "demo_section_title": {"fr": "Cas de démonstration", "en": "Demo cases"},
    "demo_section_subtitle": {
        "fr": "Cliquez sur un cas pour pré-remplir le simulateur et voir la prédiction en un clic.",
        "en": "Click a case to pre-fill the simulator and see the prediction in one click.",
    },
    "demo_try": {"fr": "Tester ce cas", "en": "Try this case"},

    "demo_blockbuster_title": {"fr": "Blockbuster franchise", "en": "Franchise blockbuster"},
    "demo_blockbuster_desc": {
        "fr": "Suite d'une saga action, gros budget, sortie estivale, cast reconnu. "
              "Le profil classique des hits Hollywood.",
        "en": "Action saga sequel, large budget, summer release, well-known cast. "
              "The classic Hollywood hit profile.",
    },
    "demo_indie_title": {"fr": "Drame indépendant", "en": "Indie drama"},
    "demo_indie_desc": {
        "fr": "Petit budget, sortie automne, cast restreint. Le pari sur la critique "
              "plutôt que le grand public.",
        "en": "Small budget, fall release, intimate cast. A critical play "
              "rather than a mass-market shot.",
    },
    "demo_horror_title": {"fr": "Horreur petit budget", "en": "Low-budget horror"},
    "demo_horror_desc": {
        "fr": "Stratégie ROI : budget très bas, fenêtre d'Halloween, signal de "
              "rentabilité historiquement fort.",
        "en": "ROI strategy: very low budget, Halloween window, historically strong "
              "profitability signal.",
    },

    # Compare extras
    "compare_winner_score": {"fr": "Score hit", "en": "Hit score"},
    "compare_outcome_dist": {"fr": "Distribution des issues", "en": "Outcome distribution"},

    # Result extras
    "result_hit_score": {"fr": "Score de potentiel hit", "en": "Hit-potential score"},
    "result_hit_score_desc": {
        "fr": "Probabilité que le film soit un hit (ROI ≥ 2). 0 = improbable, 100 = très probable.",
        "en": "Probability of being a hit (ROI ≥ 2). 0 = unlikely, 100 = very likely.",
    },

    # Insights / charts
    "insights_filter_genre": {"fr": "Filtrer par genre", "en": "Filter by genre"},
    "insights_filter_decade": {"fr": "Filtrer par décennie", "en": "Filter by decade"},
    "insights_filter_class": {"fr": "Filtrer par issue", "en": "Filter by outcome"},
    "insights_kpi_films": {"fr": "Films", "en": "Movies"},
    "insights_kpi_hit_rate": {"fr": "Taux de hit", "en": "Hit rate"},
    "insights_kpi_avg_budget": {"fr": "Budget médian", "en": "Median budget"},
    "insights_kpi_avg_roi": {"fr": "ROI médian", "en": "Median ROI"},
    "insights_chart_class_volume": {"fr": "Volume par classe", "en": "Volume per class"},
    "insights_chart_budget_roi": {"fr": "Budget vs log-ROI", "en": "Budget vs log-ROI"},
    "insights_chart_genre_class": {"fr": "Mix d'issues par genre", "en": "Outcome mix per genre"},
    "insights_chart_month_roi": {"fr": "ROI médian par mois", "en": "Median ROI by month"},
    "insights_chart_decade_hit": {"fr": "Taux de hit par décennie", "en": "Hit rate by decade"},
    "insights_caption_class_volume": {
        "fr": "Combien de films dans chaque classe sur le corpus filtré. Le dataset est déséquilibré : on a beaucoup plus de flops que de hits.",
        "en": "How many films fall in each class for the filtered corpus. The dataset is imbalanced: many more flops than hits.",
    },
    "insights_caption_budget_roi": {
        "fr": "Chaque point = un film. Axes en échelle log. Lecture : un gros budget ne garantit pas un ROI élevé — les hits à petit budget existent (en haut à gauche).",
        "en": "Each dot = one movie. Log-log axes. Read: a big budget does not guarantee a high ROI — small-budget hits exist (top-left).",
    },
    "insights_caption_genre_class": {
        "fr": "Pour chaque genre, part de flops / moyens / hits. Horreur et animation surperforment, drame et documentaire sont plus risqués.",
        "en": "For each genre, share of flops / averages / hits. Horror and animation outperform; drama and documentary are riskier.",
    },
    "insights_caption_month_roi": {
        "fr": "ROI médian par mois de sortie. Les sorties estivales et de fin d'année concentrent les meilleurs ROI — c'est la saisonnalité du box-office.",
        "en": "Median ROI by release month. Summer and holiday releases concentrate the best ROI — the box-office seasonality effect.",
    },
    "insights_caption_decade_hit": {
        "fr": "Pourcentage de hits par décennie. Le taux fluctue entre 25 % et 35 % — pas de tendance temporelle marquée dans TMDB.",
        "en": "Hit rate per decade. The rate fluctuates between 25% and 35% — no strong temporal trend in TMDB.",
    },
}
