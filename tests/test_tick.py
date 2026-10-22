from datetime import datetime, timezone

from fpl_radar_eval.io import snapshot_fingerprint, snapshots_equivalent
from fpl_radar_eval.tick import (
    missing_score_jobs,
    missing_snapshot_variants,
    score_event_ids,
    snapshot_decision,
    tick_variant_slugs,
    variants_to_build,
    variants_to_snapshot,
)

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def _boot(*events: dict) -> dict:
    return {"events": list(events)}


def test_snapshot_before_deadline_for_next_unfinished_gw() -> None:
    boot = _boot(
        {"id": 7, "finished": True, "deadline_time": "2026-10-17T10:00:00Z"},
        {
            "id": 8,
            "finished": False,
            "is_next": True,
            "deadline_time": "2026-10-23T17:30:00Z",
        },
    )
    fixtures = [{"event": 8, "kickoff_time": "2026-10-24T14:00:00Z"}]
    decision = snapshot_decision(boot, fixtures, NOW, snapshot_exists=lambda _e, _s: False)
    assert decision is not None
    assert decision["event_id"] == 8
    assert decision["late"] is False
    assert "default" in decision["missing_variants"]


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


def test_skip_if_snapshot_exists_after_kickoff() -> None:
    boot = _boot(
        {"id": 6, "finished": True, "deadline_time": "2026-10-01T10:00:00Z"},
        {"id": 7, "finished": False, "deadline_time": "2026-10-18T10:00:00Z"},
    )
    fixtures = [{"event": 7, "kickoff_time": "2026-10-18T11:00:00Z"}]
    assert (
        snapshot_decision(
            boot, fixtures, NOW, snapshot_exists=lambda eid, slug: eid == 7
        )
        is None
    )


def test_rebuild_existing_before_kickoff() -> None:
    slugs = variants_to_build(8, False, lambda _eid, _slug: True)
    assert slugs == list(tick_variant_slugs())


def test_fingerprint_ignores_taken_at() -> None:
    base = {
        "player_id": 1,
        "predicted": 4.1234567,
        "ep_next": 1.3,
        "predicted_components": {"minutes": 1.96},
    }
    left = [{**base, "taken_at": "2026-10-22T00:00:00+00:00", "late": False}]
    right = [{**base, "taken_at": "2026-10-22T12:00:00+00:00", "late": True}]
    assert snapshots_equivalent(left, right)
    changed = [{**base, "predicted": 5.0, "taken_at": left[0]["taken_at"]}]
    assert snapshot_fingerprint(left) != snapshot_fingerprint(changed)


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
