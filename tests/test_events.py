from datetime import datetime, timezone

from fpl_radar_eval.events import (
    bonus_added,
    first_kickoff,
    latest_finished_event_id,
    next_unfinished_event_id,
    parse_utc,
)


def test_next_unfinished_and_latest_finished() -> None:
    boot = {
        "events": [
            {"id": 1, "finished": True},
            {"id": 2, "finished": True},
            {"id": 3, "finished": False},
        ]
    }
    assert latest_finished_event_id(boot) == 2
    assert next_unfinished_event_id(boot) == 3


def test_parse_utc_and_first_kickoff() -> None:
    assert parse_utc("2026-10-18T11:00:00Z") == datetime(2026, 10, 18, 11, 0, tzinfo=timezone.utc)
    fixtures = [
        {"event": 7, "kickoff_time": "2026-10-18T14:00:00Z"},
        {"event": 7, "kickoff_time": "2026-10-18T11:30:00Z"},
        {"event": 8, "kickoff_time": "2026-10-25T11:00:00Z"},
    ]
    assert first_kickoff(fixtures, 7) == datetime(2026, 10, 18, 11, 30, tzinfo=timezone.utc)


def test_bonus_added() -> None:
    status = {"status": [{"event": 6, "bonus_added": False}, {"event": 6, "bonus_added": True}]}
    assert bonus_added(status, 6) is True
    assert bonus_added(status, 7) is False
