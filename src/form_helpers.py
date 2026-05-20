"""Shared form fields, presets, drivers and inference helpers for predict/compare pages."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st

import config
from ui_styles import ICONS, t


GENRE_OPTIONS = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery",
    "Romance", "Science Fiction", "Thriller", "War", "Western",
]

LANG_OPTIONS = ["en", "fr", "es", "de", "ja", "hi", "zh", "ko", "it", "ru"]


PRESETS: dict[str, dict[str, Any]] = {
    "preset_indie_drama": {
        "budget": 8_000_000, "runtime": 105, "main_genre": "Drama", "original_language": "en",
        "release_month": 10, "release_quarter": 4, "genre_count": 1,
        "production_company_count": 1, "production_country_count": 1, "spoken_language_count": 1,
        "cast_size": 12, "crew_size": 15, "writer_count": 2, "director_name": "__missing__",
        "known_actor_count": 1, "top_billed_cast_count": 3,
        "possible_franchise_flag": 0, "ensemble_cast_flag": 0, "top_director_flag": 0,
    },
    "preset_franchise_action": {
        "budget": 150_000_000, "runtime": 128, "main_genre": "Action", "original_language": "en",
        "release_month": 7, "release_quarter": 3, "genre_count": 2,
        "production_company_count": 4, "production_country_count": 2, "spoken_language_count": 1,
        "cast_size": 45, "crew_size": 80, "writer_count": 4, "director_name": "Steven Spielberg",
        "known_actor_count": 6, "top_billed_cast_count": 8,
        "possible_franchise_flag": 1, "ensemble_cast_flag": 1, "top_director_flag": 1,
    },
    "preset_low_budget_horror": {
        "budget": 5_000_000, "runtime": 92, "main_genre": "Horror", "original_language": "en",
        "release_month": 10, "release_quarter": 4, "genre_count": 1,
        "production_company_count": 1, "production_country_count": 1, "spoken_language_count": 1,
        "cast_size": 10, "crew_size": 18, "writer_count": 2, "director_name": "__missing__",
        "known_actor_count": 0, "top_billed_cast_count": 2,
        "possible_franchise_flag": 0, "ensemble_cast_flag": 0, "top_director_flag": 0,
    },
    "preset_animation_family": {
        "budget": 90_000_000, "runtime": 95, "main_genre": "Animation", "original_language": "en",
        "release_month": 6, "release_quarter": 2, "genre_count": 2,
        "production_company_count": 2, "production_country_count": 1, "spoken_language_count": 2,
        "cast_size": 20, "crew_size": 55, "writer_count": 5, "director_name": "Robert Zemeckis",
        "known_actor_count": 3, "top_billed_cast_count": 5,
        "possible_franchise_flag": 1, "ensemble_cast_flag": 0, "top_director_flag": 1,
    },
    "preset_ensemble": {
        "budget": 200_000_000, "runtime": 138, "main_genre": "Adventure", "original_language": "en",
        "release_month": 5, "release_quarter": 2, "genre_count": 3,
        "production_company_count": 5, "production_country_count": 3, "spoken_language_count": 2,
        "cast_size": 60, "crew_size": 120, "writer_count": 6, "director_name": "Peter Jackson",
        "known_actor_count": 8, "top_billed_cast_count": 10,
        "possible_franchise_flag": 1, "ensemble_cast_flag": 1, "top_director_flag": 1,
    },
    "preset_romcom": {
        "budget": 35_000_000, "runtime": 100, "main_genre": "Romance", "original_language": "en",
        "release_month": 2, "release_quarter": 1, "genre_count": 2,
        "production_company_count": 2, "production_country_count": 1, "spoken_language_count": 1,
        "cast_size": 18, "crew_size": 30, "writer_count": 3, "director_name": "__missing__",
        "known_actor_count": 2, "top_billed_cast_count": 4,
        "possible_franchise_flag": 0, "ensemble_cast_flag": 0, "top_director_flag": 0,
    },
}


def preset_options(include_custom: bool = True) -> list[str]:
    keys = list(PRESETS.keys())
    if include_custom:
        keys = ["preset_custom"] + keys
    return keys


def preset_label(key: str) -> str:
    return t(key)


def empty_defaults() -> dict[str, Any]:
    """Sensible empty-form defaults, also used as fallback when artifacts absent."""
    return dict(PRESETS["preset_indie_drama"])


def model_input_defaults() -> dict[str, Any]:
    """Defaults from the saved training artifacts (medians/modes from train set)."""
    try:
        import model_io
        artifacts = model_io.load_model(config.TRAIN_ARTIFACTS_FILE)
        return dict(artifacts.get("input_defaults", {}))
    except Exception:
        return {}


def director_options() -> list[str]:
    """Director names available in the training corpus (sorted)."""
    try:
        import model_io
        artifacts = model_io.load_model(config.TRAIN_ARTIFACTS_FILE)
    except Exception:
        return []
    names: set[str] = set()
    for key in ("director_bucket_top_names", "top_directors"):
        for n in artifacts.get(key, []):
            s = str(n).strip()
            if s and s not in ("__missing__", "__other__"):
                names.add(s)
    for n in artifacts.get("director_movie_count_map", {}):
        s = str(n).strip()
        if s and s not in ("__missing__", "__other__"):
            names.add(s)
    return sorted(names)


# ----------------------------------------------------------------------------
# Drivers (interpretation pills)
# ----------------------------------------------------------------------------

def compute_drivers(inputs: dict[str, Any]) -> list[tuple[str, str]]:
    """Return list of (label, direction) used to render driver pills.

    direction ∈ {'up', 'down', 'neutral'}.
    """
    drivers: list[tuple[str, str]] = []

    try:
        budget = float(inputs.get("budget", 0) or 0)
    except (TypeError, ValueError):
        budget = 0.0
    if budget >= 100_000_000:
        drivers.append((t("driver_budget_high"), "up"))
    elif budget > 0 and budget <= 15_000_000:
        drivers.append((t("driver_budget_low"), "neutral"))

    if int(inputs.get("possible_franchise_flag", 0) or 0) == 1:
        drivers.append((t("driver_franchise"), "up"))

    try:
        ka = int(inputs.get("known_actor_count", 0) or 0)
    except (TypeError, ValueError):
        ka = 0
    if ka >= 4:
        drivers.append((t("driver_known_actors_many"), "up"))
    elif ka == 0:
        drivers.append((t("driver_known_actors_none"), "down"))

    if int(inputs.get("top_director_flag", 0) or 0) == 1:
        drivers.append((t("driver_top_director"), "up"))

    if int(inputs.get("ensemble_cast_flag", 0) or 0) == 1:
        drivers.append((t("driver_ensemble"), "up"))

    try:
        month = int(inputs.get("release_month", 0) or 0)
    except (TypeError, ValueError):
        month = 0
    if month in (6, 7, 8):
        drivers.append((t("driver_summer"), "up"))
    elif month in (11, 12):
        drivers.append((t("driver_holiday"), "up"))

    try:
        runtime = float(inputs.get("runtime", 0) or 0)
    except (TypeError, ValueError):
        runtime = 0.0
    if runtime and runtime < 90:
        drivers.append((t("driver_short"), "neutral"))
    elif runtime and runtime > 135:
        drivers.append((t("driver_long"), "neutral"))

    try:
        pcc = int(inputs.get("production_company_count", 0) or 0)
    except (TypeError, ValueError):
        pcc = 0
    if pcc >= 4:
        drivers.append((t("driver_multi_company"), "up"))

    if not drivers:
        drivers.append((t("driver_default"), "neutral"))
    return drivers


def add_release_season(inputs: dict[str, Any]) -> dict[str, Any]:
    """Derive release_season from release_month for comparables module."""
    out = dict(inputs)
    try:
        m = int(out.get("release_month", 0) or 0)
    except (TypeError, ValueError):
        m = 0
    if m in (12, 1, 2):
        out["release_season"] = "winter"
    elif m in (3, 4, 5):
        out["release_season"] = "spring"
    elif m in (6, 7, 8):
        out["release_season"] = "summer"
    elif m in (9, 10, 11):
        out["release_season"] = "fall"
    else:
        out["release_season"] = "__missing__"
    return out


# ----------------------------------------------------------------------------
# Form rendering helpers
# ----------------------------------------------------------------------------

def _int_default(d: dict, key: str, fallback: int) -> int:
    try:
        return int(float(d.get(key, fallback)))
    except (TypeError, ValueError):
        return fallback


def _yes_no(label: str, key: str, current: int, help_text: str | None = None) -> int:
    val = st.radio(
        label,
        [0, 1],
        index=int(bool(current)),
        format_func=lambda v: ("✓ " + t("yes")) if v else ("✗ " + t("no")),
        key=key,
        horizontal=True,
        help=help_text,
    )
    return int(val)


def _director_label(name: str) -> str:
    if name == "__missing__":
        return t("field_director_unknown")
    if name == "__custom__":
        return t("field_director_custom")
    return name


def _format_budget_short(value: int | float) -> str:
    """Compact label (e.g. $1.5M) — used where space is tight."""
    v = float(value)
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        amount = v / 1_000_000
        return f"${amount:.0f}M" if amount >= 10 else f"${amount:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${int(v)}"


def _format_budget_display(value: int | float) -> str:
    """Full amount with thousands separators (slider labels)."""
    from ui_styles import get_lang

    v = int(value)
    if v == 0:
        return "0 $" if get_lang() == "fr" else "$0"
    if get_lang() == "fr":
        return f"{v:,}".replace(",", " ") + " $"
    return f"${v:,}"


BUDGET_STEP = 500_000


def _budget_options() -> list[int]:
    """Budget choices: fine steps up to 50 M$, coarser above (easy low-budget picks)."""
    low = list(range(0, 50_000_001, BUDGET_STEP))
    mid = list(range(55_000_000, 105_000_000, 5_000_000))
    high = list(range(110_000_000, 401_000_000, 10_000_000))
    # Preset values that fall between coarse steps
    extras = [
        65_000_000,
        80_000_000,
        90_000_000,
        120_000_000,
        150_000_000,
        175_000_000,
        200_000_000,
        250_000_000,
        300_000_000,
        350_000_000,
    ]
    return sorted(set(low + mid + high + extras))


def _snap_budget_to_options(value: int | float, options: list[int]) -> int:
    cur = int(value or 0)
    return min(options, key=lambda x: abs(x - cur))


def budget_slider(current: int | float, key: str) -> int:
    """Budget selector — 500 k$ steps from 0 to 50 M$, then coarser up to 400 M$."""
    options = _budget_options()
    snapped = _snap_budget_to_options(current, options)
    chosen = st.select_slider(
        f"{ICONS['budget']} {t('field_budget')}",
        options=options,
        value=snapped,
        format_func=_format_budget_display,
        key=key,
        help=t("field_budget_help") if "field_budget_help" in _has_translation() else None,
    )
    return int(chosen)


def _has_translation() -> set[str]:
    from ui_styles import TRANSLATIONS
    return set(TRANSLATIONS.keys())


def director_input(current: str, key: str) -> str:
    """Autocomplete-style director picker.

    Renders a text input that fuzzy-matches against the known director list.
    Falls back to the raw text if no exact match (handled at inference as
    `__missing__` if not in the trained vocabulary).
    """
    options = director_options()
    if current in ("__missing__", "__other__", "", None):
        default_text = ""
    else:
        default_text = current

    raw = st.text_input(
        f"{ICONS['director']} {t('field_director')}",
        value=default_text,
        placeholder=t("field_director_placeholder") if "field_director_placeholder" in _has_translation() else "ex: Christopher Nolan",
        key=f"{key}_text",
        help=t("field_director_help") if "field_director_help" in _has_translation() else None,
    ).strip()

    if not raw:
        return "__missing__"

    # exact match
    lower = raw.lower()
    matched = next((o for o in options if o.lower() == lower), None)
    if matched:
        st.caption(f"✓ {matched} {t('field_director_known') if 'field_director_known' in _has_translation() else ''}")
        return matched

    # fuzzy candidates (prefix / contains)
    candidates: list[str] = []
    for opt in options:
        if opt.lower().startswith(lower) or lower in opt.lower():
            candidates.append(opt)
            if len(candidates) >= 6:
                break
    if candidates:
        pick = st.selectbox(
            t("field_director_suggestions") if "field_director_suggestions" in _has_translation() else "Suggestions:",
            ["__keep__"] + candidates,
            format_func=lambda v: (raw + " " + (t("field_director_use_as_custom") if "field_director_use_as_custom" in _has_translation() else "(use as typed)")) if v == "__keep__" else v,
            key=f"{key}_pick",
        )
        if pick != "__keep__":
            return pick
    return raw or "__missing__"


_MONTH_LABELS_FR = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
_MONTH_LABELS_EN = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _month_label(idx: int) -> str:
    from ui_styles import get_lang
    return (_MONTH_LABELS_FR if get_lang() == "fr" else _MONTH_LABELS_EN)[idx]


def step_project(defaults: dict[str, Any], key_prefix: str = "p1") -> dict[str, Any]:
    # Row 1 — budget (slider full width) + runtime + genre_count
    budget = budget_slider(_int_default(defaults, "budget", 50_000_000), key=f"{key_prefix}_budget")

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        runtime = st.slider(
            f"{ICONS['runtime']} {t('field_runtime')}",
            min_value=60, max_value=210,
            value=_int_default(defaults, "runtime", 110),
            step=5,
            key=f"{key_prefix}_runtime",
        )
    with c2:
        genre_count = st.slider(
            f"{ICONS['genre']} {t('field_genre_count')}",
            min_value=1, max_value=5,
            value=_int_default(defaults, "genre_count", 2),
            key=f"{key_prefix}_gc",
        )
    with c3:
        gi = GENRE_OPTIONS.index(defaults["main_genre"]) if defaults.get("main_genre") in GENRE_OPTIONS else 0
        main_genre = st.selectbox(
            f"{ICONS['genre']} {t('field_genre')}",
            GENRE_OPTIONS, index=gi,
            key=f"{key_prefix}_genre",
        )

    # Row 2 — language + release month + quarter (auto-aligned)
    c4, c5, c6 = st.columns([1, 1.4, 1])
    with c4:
        li = LANG_OPTIONS.index(defaults["original_language"]) if defaults.get("original_language") in LANG_OPTIONS else 0
        original_language = st.selectbox(
            f"{ICONS['language']} {t('field_language')}",
            LANG_OPTIONS, index=li,
            key=f"{key_prefix}_lang",
        )
    with c5:
        month_value = _int_default(defaults, "release_month", 6)
        release_month = st.select_slider(
            f"{ICONS['release']} {t('field_release_month')}",
            options=list(range(1, 13)),
            value=month_value,
            format_func=_month_label,
            key=f"{key_prefix}_month",
        )
    with c6:
        release_quarter = ((release_month - 1) // 3) + 1
        st.metric(t("field_release_quarter"), f"Q{release_quarter}")

    return {
        "budget": budget,
        "runtime": runtime,
        "main_genre": main_genre,
        "original_language": original_language,
        "release_month": release_month,
        "release_quarter": release_quarter,
        "genre_count": genre_count,
    }


def step_production(defaults: dict[str, Any], key_prefix: str = "p2") -> dict[str, Any]:
    c1, c2 = st.columns(2)
    with c1:
        production_company_count = st.slider(
            f"{ICONS['production']} {t('field_prod_companies')}",
            min_value=1, max_value=8,
            value=_int_default(defaults, "production_company_count", 2),
            key=f"{key_prefix}_pcc",
        )
        production_country_count = st.slider(
            f"🌍 {t('field_prod_countries')}",
            min_value=1, max_value=5,
            value=_int_default(defaults, "production_country_count", 1),
            key=f"{key_prefix}_pco",
        )
        spoken_language_count = st.slider(
            f"{ICONS['language']} {t('field_spoken_languages')}",
            min_value=1, max_value=4,
            value=_int_default(defaults, "spoken_language_count", 1),
            key=f"{key_prefix}_slc",
        )
    with c2:
        cast_size = st.slider(
            f"{ICONS['cast']} {t('field_cast_size')}",
            min_value=5, max_value=80,
            value=_int_default(defaults, "cast_size", 25),
            step=5,
            key=f"{key_prefix}_cast",
        )
        crew_size = st.slider(
            f"{ICONS['crew']} {t('field_crew_size')}",
            min_value=5, max_value=150,
            value=_int_default(defaults, "crew_size", 20),
            step=5,
            key=f"{key_prefix}_crew",
        )
        writer_count = st.slider(
            f"{ICONS['writers']} {t('field_writer_count')}",
            min_value=1, max_value=8,
            value=_int_default(defaults, "writer_count", 3),
            key=f"{key_prefix}_wri",
        )
    return {
        "production_company_count": production_company_count,
        "production_country_count": production_country_count,
        "spoken_language_count": spoken_language_count,
        "cast_size": cast_size,
        "crew_size": crew_size,
        "writer_count": writer_count,
    }


def step_talent(defaults: dict[str, Any], key_prefix: str = "p3") -> dict[str, Any]:
    director_name = director_input(
        str(defaults.get("director_name", "__missing__")),
        key=f"{key_prefix}_director",
    )
    c1, c2 = st.columns(2)
    with c1:
        known_actor_count = st.slider(
            f"{ICONS['cast']} {t('field_known_actors')}",
            min_value=0, max_value=10,
            value=_int_default(defaults, "known_actor_count", 2),
            key=f"{key_prefix}_ka",
        )
        top_billed_cast_count = st.slider(
            f"{ICONS['top']} {t('field_top_billed')}",
            min_value=0, max_value=15,
            value=_int_default(defaults, "top_billed_cast_count", 4),
            key=f"{key_prefix}_tb",
            help=t("field_top_billed_help") if "field_top_billed_help" in _has_translation() else None,
        )
    with c2:
        possible_franchise_flag = _yes_no(
            f"{ICONS['franchise']} {t('field_franchise')}",
            f"{key_prefix}_franch",
            _int_default(defaults, "possible_franchise_flag", 0),
        )
        ensemble_cast_flag = _yes_no(
            f"{ICONS['ensemble']} {t('field_ensemble')}",
            f"{key_prefix}_ens",
            _int_default(defaults, "ensemble_cast_flag", 0),
            help_text=t("field_ensemble_help") if "field_ensemble_help" in _has_translation() else None,
        )
        top_director_flag = _yes_no(
            f"{ICONS['top']} {t('field_top_director')}",
            f"{key_prefix}_td",
            _int_default(defaults, "top_director_flag", 0),
        )
    return {
        "director_name": director_name,
        "known_actor_count": known_actor_count,
        "top_billed_cast_count": top_billed_cast_count,
        "possible_franchise_flag": possible_franchise_flag,
        "ensemble_cast_flag": ensemble_cast_flag,
        "top_director_flag": top_director_flag,
    }


def render_compact_form(defaults: dict[str, Any], key_prefix: str) -> dict[str, Any]:
    """Compact single-screen form for the Compare page."""
    with st.expander("Project", expanded=True):
        proj = step_project(defaults, key_prefix=f"{key_prefix}_proj")
    with st.expander("Production"):
        prod = step_production({**defaults, **proj}, key_prefix=f"{key_prefix}_prod")
    with st.expander("Talent & packaging"):
        talent = step_talent({**defaults, **proj, **prod}, key_prefix=f"{key_prefix}_tal")
    return {**proj, **prod, **talent}
