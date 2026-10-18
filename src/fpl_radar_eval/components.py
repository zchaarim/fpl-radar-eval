from __future__ import annotations

from typing import Any

from fpl_radar.features import minutes_points
from fpl_radar.fpl_rules import ELEMENT_TYPE_DEF, ELEMENT_TYPE_GKP, scoring_table
from fpl_radar.models import PlayerXp
from fpl_radar.xp.model import CS_KEYS, GOAL_KEYS

COMPONENT_KEYS = (
    "minutes",
    "attack",
    "cs",
    "gc",
    "defcon",
    "bonus",
    "saves",
    "cards",
)

_GC_TYPES = {ELEMENT_TYPE_GKP, ELEMENT_TYPE_DEF}


def empty_components() -> dict[str, float]:
    return {key: 0.0 for key in COMPONENT_KEYS}


def predicted_components(
    xp: PlayerXp,
    event_id: int,
    element_type: int,
    table: dict[str, int | float] | None = None,
) -> dict[str, float]:
    """Map ``expected_points`` event breakdown onto scorable component points."""
    table = table or scoring_table()
    out = empty_components()
    if xp.placeholder:
        return out
    event = (xp.breakdown.get("events") or {}).get(str(int(event_id))) or {}
    if event.get("blank"):
        return out
    p_played = float(event.get("p_played") or 0.0)
    p60 = float(event.get("p60") or 0.0)
    out["minutes"] = minutes_points(p_played, p60, table)
    goal_pts = float(table[GOAL_KEYS.get(element_type, "goal_mid")])
    assist_pts = float(table["assist"])
    out["attack"] = float(event.get("xg") or 0.0) * goal_pts + float(event.get("xa") or 0.0) * assist_pts
    out["cs"] = float(event.get("cs_xp") or 0.0)
    out["gc"] = float(event.get("gc_xp") or 0.0)
    out["defcon"] = float(event.get("defcon_xp") or 0.0)
    out["bonus"] = float(event.get("bonus_xp") or 0.0)
    out["saves"] = float(event.get("saves_xp") or 0.0)
    out["cards"] = float(event.get("cards_xp") or 0.0)
    return out


def actual_components(
    stats: dict[str, Any],
    element_type: int,
    table: dict[str, int | float] | None = None,
) -> dict[str, float]:
    """FPL live ``stats`` → the same component keys the model predicts.

    Own goals and penalty save/miss are **other** (returned separately); the
    model does not predict them.
    """
    table = table or scoring_table()
    minutes = float(stats.get("minutes") or 0)
    out = empty_components()
    if minutes <= 0:
        return out

    if minutes >= 60:
        out["minutes"] = float(table["minutes_60_plus"])
    else:
        out["minutes"] = float(table["minutes_0_59"])

    goal_pts = float(table[GOAL_KEYS.get(element_type, "goal_mid")])
    out["attack"] = float(stats.get("goals_scored") or 0) * goal_pts + float(
        stats.get("assists") or 0
    ) * float(table["assist"])
    cs_pts = float(table[CS_KEYS.get(element_type, "clean_sheet_fwd")])
    out["cs"] = float(stats.get("clean_sheets") or 0) * cs_pts
    if element_type in _GC_TYPES:
        conceded = int(stats.get("goals_conceded") or 0)
        per = int(table["goals_conceded_per"])
        out["gc"] = float(conceded // per) * float(table["goals_conceded_points"])
    if element_type != ELEMENT_TYPE_GKP and minutes >= 60:
        threshold = int(
            table["defcon_def_threshold"]
            if element_type == ELEMENT_TYPE_DEF
            else table["defcon_mid_fwd_threshold"]
        )
        actions = float(stats.get("defensive_contribution") or 0)
        if actions >= threshold:
            out["defcon"] = float(table["defcon_points"])
    out["bonus"] = float(stats.get("bonus") or 0)
    if element_type == ELEMENT_TYPE_GKP:
        saves = int(stats.get("saves") or 0)
        per = int(table["save_per"])
        out["saves"] = float(saves // per) * float(table["save_points"])
    out["cards"] = float(stats.get("yellow_cards") or 0) * float(table["yellow_card"]) + float(
        stats.get("red_cards") or 0
    ) * float(table["red_card"])
    return out


def other_points(stats: dict[str, Any], table: dict[str, int | float] | None = None) -> float:
    table = table or scoring_table()
    return (
        float(stats.get("own_goals") or 0) * float(table["own_goal"])
        + float(stats.get("penalties_saved") or 0) * float(table["penalty_save"])
        + float(stats.get("penalties_missed") or 0) * float(table["penalty_miss"])
    )


def component_sum(parts: dict[str, float]) -> float:
    return sum(float(parts.get(key) or 0.0) for key in COMPONENT_KEYS)

