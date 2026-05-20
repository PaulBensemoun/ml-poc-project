"""Sensitivity analysis: how much does P(hit) change when we tweak a single lever?

For each scenario we deep-copy the user's baseline inputs, apply the lever
mutation, re-run the inference, and return the delta in percentage points
on the hit probability.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable

from ui_styles import t


Mutator = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class SensitivityResult:
    label_key: str
    new_p_hit: float
    delta_pp: float


def _set(d: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    out = copy.deepcopy(d)
    out.update(kwargs)
    return out


def _bump_budget(d: dict[str, Any], factor: float) -> dict[str, Any]:
    out = copy.deepcopy(d)
    try:
        b = float(out.get("budget", 0) or 0)
    except (TypeError, ValueError):
        b = 0.0
    out["budget"] = max(0.0, b * factor)
    return out


def build_scenarios(baseline: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Generate ordered (i18n_label_key, mutated_inputs) pairs.

    Skips scenarios that would have no effect on the input (e.g. enabling
    franchise flag when it is already on).

    Talent / packaging levers come first because they almost always move
    P(hit) by 1pp or more, which is what makes a sensitivity table useful
    as a decision aid. Budget perturbations come last and use ±50 % rather
    than ±20 % so the effect is visible above the model's noise floor.
    """

    scenarios: list[tuple[str, dict[str, Any]]] = []

    current_ka = int(baseline.get("known_actor_count", 0) or 0)
    scenarios.append(("sens_known_actor_plus", _set(baseline, known_actor_count=current_ka + 2)))
    if current_ka > 0:
        scenarios.append(("sens_known_actor_minus", _set(baseline, known_actor_count=0)))

    if int(baseline.get("top_director_flag", 0) or 0) == 0:
        scenarios.append(
            (
                "sens_top_director",
                _set(baseline, top_director_flag=1, director_name="Steven Spielberg"),
            )
        )

    if int(baseline.get("possible_franchise_flag", 0) or 0) == 0:
        scenarios.append(("sens_franchise_on", _set(baseline, possible_franchise_flag=1)))

    if int(baseline.get("ensemble_cast_flag", 0) or 0) == 0:
        scenarios.append(("sens_ensemble", _set(baseline, ensemble_cast_flag=1)))

    # Budget levers — use ±50 % to clear the noise floor. The direction is
    # determined by the ROI labeling: hits = ROI ≥ 2, so reducing the
    # budget (lower revenue needed to clear 2×) typically *increases*
    # P(hit) for already-credible projects.
    scenarios.append(("sens_budget_up", _bump_budget(baseline, 1.5)))
    scenarios.append(("sens_budget_down", _bump_budget(baseline, 0.5)))

    return scenarios


# Movements below this absolute delta are essentially noise from the model
# and we don't show them — they confuse rather than inform.
NOISE_FLOOR_PP = 0.5


def run_sensitivity(
    baseline_inputs: dict[str, Any],
    baseline_p_hit: float,
) -> list[SensitivityResult]:
    from inference import predict_movie_profile

    results: list[SensitivityResult] = []
    for label_key, mutated in build_scenarios(baseline_inputs):
        try:
            out = predict_movie_profile(mutated)
            p_hit = float(out["probabilities"].get("hit", 0.0))
        except Exception:
            continue
        delta_pp = (p_hit - baseline_p_hit) * 100.0
        if abs(delta_pp) < NOISE_FLOOR_PP:
            # Skip uninformative rows (noise floor).
            continue
        results.append(SensitivityResult(label_key=label_key, new_p_hit=p_hit, delta_pp=delta_pp))

    results.sort(key=lambda r: abs(r.delta_pp), reverse=True)
    return results


def to_display_rows(results: list[SensitivityResult]) -> list[tuple[str, float, float]]:
    return [(t(r.label_key), r.delta_pp, r.new_p_hit) for r in results]
