"""Generate a one-page PDF prediction report (via reportlab)."""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


BRAND_PRIMARY = colors.HexColor("#1E3A8A")
BRAND_ACCENT = colors.HexColor("#2563EB")
BRAND_SOFT = colors.HexColor("#DBEAFE")
NEUTRAL = colors.HexColor("#475569")
BORDER = colors.HexColor("#E2E8F0")
TEXT_DARK = colors.HexColor("#0F172A")
HIT_COLOR = colors.HexColor("#15803D")
AVG_COLOR = colors.HexColor("#B45309")
FLOP_COLOR = colors.HexColor("#B91C1C")


def _outcome_color(outcome: str) -> colors.Color:
    return {
        "hit": HIT_COLOR,
        "average": AVG_COLOR,
        "flop": FLOP_COLOR,
    }.get(str(outcome).lower(), NEUTRAL)


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "Title",
        parent=base["Title"],
        fontSize=20,
        leading=24,
        textColor=BRAND_PRIMARY,
        spaceAfter=4,
    )
    subtitle = ParagraphStyle(
        "Subtitle",
        parent=base["Normal"],
        fontSize=10,
        leading=12,
        textColor=NEUTRAL,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontSize=12,
        leading=15,
        textColor=BRAND_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=9.5,
        leading=13,
        textColor=TEXT_DARK,
    )
    small = ParagraphStyle(
        "Small",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
        textColor=NEUTRAL,
    )
    return {"title": title, "subtitle": subtitle, "h2": h2, "body": body, "small": small}


def _format_money(value: Any) -> str:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if v <= 0:
        return "—"
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:,.0f}"


def _format_pct(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value)*100:.{decimals}f}%"
    except (TypeError, ValueError):
        return "—"


def build_report_pdf(
    *,
    project_name: str,
    user_inputs: dict[str, Any],
    prediction: dict[str, Any],
    drivers: list[str],
    sensitivity_rows: list[tuple[str, float, float]],
    comparables: pd.DataFrame | None,
    lang: str = "fr",
) -> bytes:
    """Build a 1-page PDF report and return its bytes."""

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="CinéSignal — Movie Success Report",
        author="CinéSignal",
    )
    s = _styles()
    is_fr = lang == "fr"
    story: list[Any] = []

    # Header
    story.append(Paragraph("CinéSignal — Movie Success Report", s["title"]))
    subtitle_text = (
        f"{'Projet' if is_fr else 'Project'}: <b>{project_name}</b> · "
        f"{'Généré le' if is_fr else 'Generated on'} {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    story.append(Paragraph(subtitle_text, s["subtitle"]))

    # Outcome banner
    outcome = str(prediction.get("prediction", "—")).lower()
    outcome_label = {
        "hit": ("HIT — fort potentiel" if is_fr else "HIT — strong potential"),
        "average": ("MOYEN — rentabilité incertaine" if is_fr else "AVERAGE — uncertain profitability"),
        "flop": ("FLOP — risque élevé" if is_fr else "FLOP — high risk"),
    }.get(outcome, outcome.upper())
    confidence = float(prediction.get("confidence", 0.0))
    outcome_table = Table(
        [
            [
                Paragraph(
                    f"<b>{'Issue prédite' if is_fr else 'Predicted outcome'}</b><br/>"
                    f'<font size="14" color="{_outcome_color(outcome).hexval()}">{outcome_label}</font>',
                    s["body"],
                ),
                Paragraph(
                    f"<b>{'Confiance' if is_fr else 'Confidence'}</b><br/>"
                    f'<font size="14">{_format_pct(confidence, 1)}</font>',
                    s["body"],
                ),
                Paragraph(
                    f"<b>{'Risque' if is_fr else 'Risk'}</b><br/>"
                    f'<font size="9">{prediction.get("risk_level", "—")}</font>',
                    s["body"],
                ),
            ]
        ],
        colWidths=[6.5 * cm, 4.0 * cm, 6.5 * cm],
    )
    outcome_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(outcome_table)
    story.append(Spacer(1, 0.3 * cm))

    # Probabilities
    story.append(Paragraph(("Distribution des probabilités" if is_fr else "Probability distribution"), s["h2"]))
    probs = prediction.get("probabilities", {})
    prob_rows = [["Flop", _format_pct(probs.get("flop", 0)), "Average", _format_pct(probs.get("average", 0)), "Hit", _format_pct(probs.get("hit", 0))]]
    prob_table = Table(prob_rows, colWidths=[2 * cm, 2 * cm, 2.5 * cm, 2 * cm, 2 * cm, 2 * cm])
    prob_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, 0), FLOP_COLOR),
                ("TEXTCOLOR", (2, 0), (2, 0), AVG_COLOR),
                ("TEXTCOLOR", (4, 0), (4, 0), HIT_COLOR),
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, 0), "Helvetica-Bold"),
                ("FONTNAME", (4, 0), (4, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(prob_table)

    # Interpretation
    story.append(Paragraph(("Interprétation business" if is_fr else "Business interpretation"), s["h2"]))
    story.append(Paragraph(prediction.get("business_interpretation", "—"), s["body"]))

    # Project profile
    story.append(Paragraph(("Profil du projet" if is_fr else "Project profile"), s["h2"]))
    field_rows = [
        [
            ("Budget" if is_fr else "Budget"),
            _format_money(user_inputs.get("budget")),
            ("Durée" if is_fr else "Runtime"),
            f"{user_inputs.get('runtime', '—')} min",
        ],
        [
            ("Genre" if is_fr else "Genre"),
            str(user_inputs.get("main_genre", "—")),
            ("Langue" if is_fr else "Language"),
            str(user_inputs.get("original_language", "—")),
        ],
        [
            ("Cast" if is_fr else "Cast"),
            str(user_inputs.get("cast_size", "—")),
            ("Crew" if is_fr else "Crew"),
            str(user_inputs.get("crew_size", "—")),
        ],
        [
            ("Acteurs reconnus" if is_fr else "Known actors"),
            str(user_inputs.get("known_actor_count", "—")),
            ("Franchise" if is_fr else "Franchise"),
            (("Oui" if is_fr else "Yes") if int(user_inputs.get("possible_franchise_flag", 0) or 0) else ("Non" if is_fr else "No")),
        ],
        [
            ("Réalisateur" if is_fr else "Director"),
            str(user_inputs.get("director_name") or "—").replace("__missing__", "—"),
            ("Réalisateur top" if is_fr else "Top director"),
            (("Oui" if is_fr else "Yes") if int(user_inputs.get("top_director_flag", 0) or 0) else ("Non" if is_fr else "No")),
        ],
    ]
    project_table = Table(field_rows, colWidths=[3.5 * cm, 4.5 * cm, 3.5 * cm, 4.5 * cm])
    project_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), NEUTRAL),
                ("TEXTCOLOR", (2, 0), (2, -1), NEUTRAL),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(project_table)

    # Drivers
    if drivers:
        story.append(Paragraph(("Facteurs explicatifs" if is_fr else "Key drivers"), s["h2"]))
        for d in drivers:
            story.append(Paragraph(f"• {d}", s["body"]))

    # Sensitivity
    if sensitivity_rows:
        story.append(Paragraph(("Analyse de sensibilité" if is_fr else "Sensitivity analysis"), s["h2"]))
        sens_data = [[("Levier" if is_fr else "Lever"), ("Nouvelle P(hit)" if is_fr else "New P(hit)"), "Δ pp"]]
        for label, delta_pp, p_hit in sensitivity_rows[:6]:
            sens_data.append([label, _format_pct(p_hit), f"{delta_pp:+.1f} pp"])
        sens_table = Table(sens_data, colWidths=[10 * cm, 3 * cm, 3 * cm])
        sens_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND_SOFT),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(sens_table)

    # Comparables
    if comparables is not None and not comparables.empty:
        story.append(Paragraph(("Films historiques comparables" if is_fr else "Comparable historical movies"), s["h2"]))
        comp_data = [
            [
                ("Titre" if is_fr else "Title"),
                ("Année" if is_fr else "Year"),
                ("Genre" if is_fr else "Genre"),
                ("Budget" if is_fr else "Budget"),
                ("Issue" if is_fr else "Outcome"),
                "Sim.",
            ]
        ]
        for _, r in comparables.iterrows():
            comp_data.append(
                [
                    str(r.get("title", "—")),
                    str(int(r["release_year"])) if pd.notna(r.get("release_year")) else "—",
                    str(r.get("main_genre", "—")),
                    _format_money(r.get("budget")),
                    str(r.get("movie_success_class", "—")).upper(),
                    _format_pct(r.get("similarity", 0), 0),
                ]
            )
        comp_table = Table(comp_data, colWidths=[5.5 * cm, 1.6 * cm, 3.2 * cm, 2.2 * cm, 2 * cm, 1.5 * cm])
        comp_table.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDER),
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND_SOFT),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(comp_table)

    # Footer disclaimer
    story.append(Spacer(1, 0.4 * cm))
    disclaimer = (
        "Outil d'aide à la décision uniquement. Les prédictions doivent être combinées "
        "avec une analyse marché et le jugement d'experts. Modèle : régression logistique "
        "enrichie crédits sur dataset TMDB."
        if is_fr
        else
        "Decision-support tool only. Predictions must be combined with market analysis "
        "and expert judgment. Model: credits-enriched logistic regression on TMDB dataset."
    )
    story.append(Paragraph(disclaimer, s["small"]))

    doc.build(story)
    return buf.getvalue()
