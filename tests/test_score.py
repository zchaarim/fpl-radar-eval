from fpl_radar.fpl_rules import ELEMENT_TYPE_MID, scoring_table

from fpl_radar_eval.score import score_snapshot


def test_score_snapshot_mae() -> None:
    table = scoring_table()
    rows = [
        {
            "player_id": 8,
            "web_name": "Test",
            "element_type": ELEMENT_TYPE_MID,
            "position": "MID",
            "placeholder": False,
            "predicted": 4.0,
            "predicted_components": {
                "minutes": 2.0,
                "attack": 1.5,
                "cs": 0.2,
                "gc": 0.0,
                "defcon": 0.1,
                "bonus": 0.2,
                "saves": 0.0,
                "cards": 0.0,
            },
            "ep_next": 3.0,
        }
    ]
    live = {
        8: {
            "minutes": 90,
            "goals_scored": 0,
            "assists": 0,
            "clean_sheets": 0,
            "goals_conceded": 1,
            "defensive_contribution": 0,
            "bonus": 0,
            "saves": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "total_points": 2,
        }
    }
    report = score_snapshot(1, rows, live, table)
    assert report["players"] == 1
    # modelled actual minutes = 2, predicted 4 → error -2
    assert report["rows"][0]["actual_modelled"] == 2.0
    assert report["model_vs_actual"]["mae"] == 2.0
    assert report["ep_next_vs_actual"]["mae"] == 1.0
    assert report["by_component"]["minutes"]["mae"] == 0.0
    assert report["by_component"]["attack"]["mae"] == 1.5
