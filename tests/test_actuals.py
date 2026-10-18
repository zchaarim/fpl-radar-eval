from fpl_radar.fpl_rules import ELEMENT_TYPE_DEF, ELEMENT_TYPE_FWD, ELEMENT_TYPE_GKP, scoring_table
from fpl_radar.models import PlayerXp

from fpl_radar_eval.components import actual_components, other_points, predicted_components


def test_defender_sixty_cs_defcon() -> None:
    stats = {
        "minutes": 90,
        "goals_scored": 0,
        "assists": 0,
        "clean_sheets": 1,
        "goals_conceded": 0,
        "defensive_contribution": 12,
        "bonus": 3,
        "saves": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 0,
    }
    parts = actual_components(stats, ELEMENT_TYPE_DEF)
    assert parts["minutes"] == 2
    assert parts["cs"] == 4
    assert parts["defcon"] == 2
    assert parts["bonus"] == 3
    assert parts["gc"] == 0


def test_defender_gc_and_cameo_no_cs() -> None:
    stats = {
        "minutes": 45,
        "goals_scored": 1,
        "assists": 1,
        "clean_sheets": 0,
        "goals_conceded": 3,
        "defensive_contribution": 20,
        "bonus": 0,
        "yellow_cards": 1,
        "red_cards": 0,
    }
    parts = actual_components(stats, ELEMENT_TYPE_DEF)
    assert parts["minutes"] == 1
    assert parts["attack"] == 6 + 3
    assert parts["cs"] == 0
    assert parts["gc"] == -1
    assert parts["defcon"] == 0
    assert parts["cards"] == -1


def test_gk_saves_and_other() -> None:
    stats = {
        "minutes": 90,
        "saves": 7,
        "clean_sheets": 0,
        "goals_conceded": 2,
        "penalties_saved": 1,
        "own_goals": 1,
        "yellow_cards": 0,
        "red_cards": 0,
        "goals_scored": 0,
        "assists": 0,
        "bonus": 0,
        "defensive_contribution": 0,
    }
    parts = actual_components(stats, ELEMENT_TYPE_GKP)
    assert parts["saves"] == 2
    assert parts["gc"] == -1
    assert parts["defcon"] == 0
    assert other_points(stats) == 5 + -2


def test_fwd_no_cs_points() -> None:
    stats = {
        "minutes": 90,
        "clean_sheets": 1,
        "goals_scored": 2,
        "assists": 0,
        "defensive_contribution": 12,
        "goals_conceded": 0,
        "bonus": 1,
        "yellow_cards": 0,
        "red_cards": 0,
    }
    parts = actual_components(stats, ELEMENT_TYPE_FWD)
    assert parts["cs"] == 0
    assert parts["attack"] == 8
    assert parts["defcon"] == 2


def test_predicted_components_from_breakdown() -> None:
    table = scoring_table()
    xp = PlayerXp(
        player_id=1,
        event_ids=[2],
        per_event={2: 4.0},
        horizon_sum=4.0,
        placeholder=False,
        breakdown={
            "events": {
                "2": {
                    "p_played": 1.0,
                    "p60": 1.0,
                    "xg": 0.5,
                    "xa": 0.0,
                    "cs_xp": 1.2,
                    "gc_xp": -0.3,
                    "defcon_xp": 0.4,
                    "bonus_xp": 0.5,
                    "saves_xp": 0.0,
                    "cards_xp": -0.1,
                }
            }
        },
    )
    parts = predicted_components(xp, 2, ELEMENT_TYPE_FWD, table)
    assert parts["minutes"] == 2.0
    assert abs(parts["attack"] - 0.5 * 4) < 1e-9
    assert parts["cs"] == 1.2
    assert parts["cards"] == -0.1
