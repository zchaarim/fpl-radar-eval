from datetime import datetime, timezone

from fpl_radar_eval.tick import (
    missing_score_jobs,
    missing_snapshot_variants,
    score_event_ids,
    snapshot_decision,
    tick_variant_slugs,
    variants_to_snapshot,
)

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def _boot(*events: dict) -> dict:
    return {"events": list(events)}


def test_no_snapshot_before_deadline() -> None:
    boot = _boot(
        {
            "id": 7,
            "finished": False,
            "deadline_time": "2026-10-18T18:00:00Z",
        }
    )
    fixtures = [{"event": 7, "kickoff_time": "2026-10-18T19:30:00Z"}]
    assert snapshot_decision(boot, fixtures, NOW, snapshot_exists=lambda _e, _s: False) is None


def test_snapshot_after_deadline_before_kickoff() -> None:
    boot = _boot(
        {
            "id": 7,
            "finished": False,
            "deadline_time": "2026-10-18T11:00:00Z",
        }
    )
    fixtures = [{"event": 7, "kickoff_time": "2026-10-18T14:00:00Z"}]
    decision = snapshot_decision(boot, fixtures, NOW, snapshot_exists=lambda _e, _s: False)
    assert decision is not None
    assert decision["event_id"] == 7
    assert decision["late"] is False
    assert "default" in decision["missing_variants"]


def test_late_snapshot_after_kickoff() -> None:
    boot = _boot(
        {
            "id": 7,
            "finished": False,
            "deadline_time": "2026-10-18T10:00:00Z",
        }
    )
    fixtures = [{"event": 7, "kickoff_time": "2026-10-18T11:30:00Z"}]
    decision = snapshot_decision(boot, fixtures, NOW, snapshot_exists=lambda _e, _s: False)
    assert decision is not None
    assert decision["late"] is True


def test_skip_if_snapshot_exists_or_finished() -> None:
    boot = _boot(
        {"id": 6, "finished": True, "deadline_time": "2026-10-01T10:00:00Z"},
        {"id": 7, "finished": False, "deadline_time": "2026-10-18T10:00:00Z"},
    )
    fixtures = [{"event": 7, "kickoff_time": "2026-10-18T19:00:00Z"}]
    assert (
        snapshot_decision(
            boot, fixtures, NOW, snapshot_exists=lambda eid, slug: eid == 7
        )
        is None
    )


def test_late_does_not_add_variants_if_any_snapshot_exists() -> None:
    have = {"default"}
    missing = variants_to_snapshot(7, True, lambda _eid, slug: slug in have)
    assert missing == []


def test_late_still_snapshots_if_nothing_exists() -> None:
    missing = variants_to_snapshot(7, True, lambda _eid, _slug: False)
    assert missing == list(tick_variant_slugs())


def test_only_missing_variants_are_listed() -> None:
    have = {"default", "minutes-k-2"}
    missing = missing_snapshot_variants(7, lambda _eid, slug: slug in have)
    assert "default" not in missing
    assert "minutes-k-2" not in missing
    assert "xgi-k-16" in missing
    assert set(tick_variant_slugs()) - have == set(missing)


def test_score_jobs_skip_existing_and_missing_snapshot() -> None:
    boot = _boot({"id": 6, "finished": True})
    status = {"status": [{"event": 6, "bonus_added": True}]}
    jobs = missing_score_jobs(
        boot,
        status,
        snapshot_exists=lambda eid, slug: eid == 6 and slug in {"default", "minutes-k-2"},
        scored_exists=lambda eid, slug: slug == "default",
    )
    assert (6, "default") not in jobs
    assert (6, "minutes-k-2") in jobs
    assert (6, "xgi-k-4") not in jobs


def test_score_when_finished_bonus_and_snapshot() -> None:
    boot = _boot(
        {"id": 6, "finished": True},
        {"id": 7, "finished": False},
    )
    status = {"status": [{"event": 6, "bonus_added": True}]}
    ids = score_event_ids(
        boot,
        status,
        snapshot_exists=lambda eid: eid == 6,
        scored_exists=lambda _e: False,
    )
    assert ids == [6]


def test_no_score_until_bonus() -> None:
    boot = _boot({"id": 6, "finished": True})
    status = {"status": [{"event": 6, "bonus_added": False}]}
    ids = score_event_ids(
        boot,
        status,
        snapshot_exists=lambda _e: True,
        scored_exists=lambda _e: False,
    )
    assert ids == []
