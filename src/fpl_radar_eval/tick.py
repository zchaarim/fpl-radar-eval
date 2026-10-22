from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fpl_radar.clients.fpl import FplClient
from fpl_radar.fpl_rules import ShrinkageConfig, shrinkage_from_overrides
from fpl_radar.ingest.sync import default_cache, load_model_context, sync_fpl, sync_understat

from fpl_radar_eval.events import bonus_added, first_kickoff
from fpl_radar_eval.io import (
    read_jsonl,
    repo_relpath,
    scored_path,
    snapshot_fingerprint,
    snapshot_path,
    snapshots_equivalent,
    write_json,
    write_jsonl,
)
from fpl_radar_eval.score import run_score
from fpl_radar_eval.snapshot import build_snapshot_rows

# Production defaults plus one-knob sweeps. Not a full grid.
TICK_SHRINKAGE: tuple[ShrinkageConfig, ...] = (
    ShrinkageConfig(),
    shrinkage_from_overrides(minutes_k=2),
    shrinkage_from_overrides(minutes_k=8),
    shrinkage_from_overrides(xgi_k=4),
    shrinkage_from_overrides(xgi_k=16),
    shrinkage_from_overrides(team_k=5),
    shrinkage_from_overrides(team_k=20),
)


def tick_variant_slugs() -> tuple[str, ...]:
    return tuple(cfg.variant_slug() for cfg in TICK_SHRINKAGE)


def snapshot_window(
    bootstrap: dict[str, Any],
    fixtures: list[dict[str, Any]],
    now: datetime,
) -> dict[str, Any] | None:
    """Next unfinished GW (usually ``is_next``). Open before deadline; ``late`` after kickoff."""
    now = now.astimezone(timezone.utc)
    for event in bootstrap.get("events") or []:
        if event.get("finished"):
            continue
        event_id = int(event["id"])
        kickoff = first_kickoff(fixtures, event_id)
        return {
            "event_id": event_id,
            "late": kickoff is not None and now >= kickoff,
            "deadline_time": event.get("deadline_time"),
            "first_kickoff": kickoff.isoformat() if kickoff else None,
        }
    return None


def snapshot_decision(
    bootstrap: dict[str, Any],
    fixtures: list[dict[str, Any]],
    now: datetime,
    *,
    snapshot_exists,
) -> dict[str, Any] | None:
    """Window plus at least one missing variant file. Used by tests and dry-run."""
    window = snapshot_window(bootstrap, fixtures, now)
    if window is None:
        return None
    missing = variants_to_build(int(window["event_id"]), bool(window["late"]), snapshot_exists)
    if not missing:
        return None
    return {**window, "missing_variants": missing}


def missing_snapshot_variants(event_id: int, snapshot_exists) -> list[str]:
    return [slug for slug in tick_variant_slugs() if not snapshot_exists(event_id, slug)]


def variants_to_snapshot(event_id: int, late: bool, snapshot_exists) -> list[str]:
    """Missing tick files. After kickoff, do not add variants if any freeze already exists."""
    missing = missing_snapshot_variants(event_id, snapshot_exists)
    if not missing:
        return []
    if late and any(snapshot_exists(event_id, slug) for slug in tick_variant_slugs()):
        return []
    return missing


def variants_to_build(event_id: int, late: bool, snapshot_exists) -> list[str]:
    """Slugs to generate: missing files, plus existing ones before kickoff (content compare)."""
    if late:
        return variants_to_snapshot(event_id, late, snapshot_exists)
    return list(tick_variant_slugs())


def missing_score_jobs(
    bootstrap: dict[str, Any],
    event_status: dict[str, Any],
    *,
    snapshot_exists,
    scored_exists,
) -> list[tuple[int, str]]:
    """Finished + bonus GWs where a snapshot exists and the score file does not."""
    jobs: list[tuple[int, str]] = []
    for event in bootstrap.get("events") or []:
        if not event.get("finished"):
            continue
        event_id = int(event["id"])
        if not bonus_added(event_status, event_id):
            continue
        for slug in tick_variant_slugs():
            if snapshot_exists(event_id, slug) and not scored_exists(event_id, slug):
                jobs.append((event_id, slug))
    return jobs


def score_event_ids(
    bootstrap: dict[str, Any],
    event_status: dict[str, Any],
    *,
    snapshot_exists,
    scored_exists,
) -> list[int]:
    """Default-variant event ids that still need a score (compat for tests)."""

    def snap(eid: int, slug: str = "default") -> bool:
        try:
            return snapshot_exists(eid, slug)
        except TypeError:
            return snapshot_exists(eid)

    def scored(eid: int, slug: str = "default") -> bool:
        try:
            return scored_exists(eid, slug)
        except TypeError:
            return scored_exists(eid)

    return sorted({eid for eid, slug in missing_score_jobs(
        bootstrap,
        event_status,
        snapshot_exists=snap,
        scored_exists=scored,
    ) if slug == "default"})


def run_tick(*, sync: bool = True, dry_run: bool = False, now: datetime | None = None) -> dict[str, Any]:
    if sync:
        sync_fpl()
        sync_understat()
    client = FplClient(cache=default_cache())
    ctx = load_model_context(client)
    status = client.event_status()
    clock = now or datetime.now(timezone.utc)
    window = snapshot_window(ctx.bootstrap, ctx.fixtures, clock)
    by_slug = {cfg.variant_slug(): cfg for cfg in TICK_SHRINKAGE}
    actions: list[dict[str, Any]] = []

    if window:
        event_id = int(window["event_id"])

        def _exists(eid: int, variant: str) -> bool:
            return snapshot_path(eid, variant=variant).exists()

        for slug in variants_to_build(event_id, bool(window["late"]), _exists):
            path = snapshot_path(event_id, variant=slug)
            already = path.exists()
            if dry_run:
                actions.append(
                    {
                        "op": "refresh" if already else "snapshot",
                        "dry_run": True,
                        "variant": slug,
                        **window,
                    }
                )
                continue
            rows, meta = build_snapshot_rows(
                event_id,
                sync=False,
                late=bool(window["late"]),
                deadline_time=window.get("deadline_time"),
                first_kickoff=window.get("first_kickoff"),
                shrinkage=by_slug[slug],
            )
            if already and snapshots_equivalent(read_jsonl(path), rows):
                actions.append(
                    {
                        "op": "unchanged",
                        "variant": slug,
                        "path": repo_relpath(path),
                        **window,
                    }
                )
                continue
            write_jsonl(path, rows)
            write_json(
                path.with_suffix(".meta.json"),
                {
                    **meta,
                    **window,
                    "path": repo_relpath(path),
                    "content_hash": snapshot_fingerprint(rows),
                    "replaced": already,
                },
            )
            actions.append(
                {
                    "op": "refresh" if already else "snapshot",
                    "path": repo_relpath(path),
                    **meta,
                    **window,
                }
            )

    jobs = missing_score_jobs(
        ctx.bootstrap,
        status,
        snapshot_exists=lambda eid, slug: snapshot_path(eid, variant=slug).exists(),
        scored_exists=lambda eid, slug: scored_path(eid, variant=slug).exists(),
    )
    for event_id, slug in jobs:
        if dry_run:
            actions.append({"op": "score", "event_id": event_id, "variant": slug, "dry_run": True})
            continue
        report = run_score(event_id, variant=slug)
        out = scored_path(event_id, variant=slug)
        payload = {k: v for k, v in report.items() if k != "rows"}
        write_json(out, payload)
        actions.append(
            {
                "op": "score",
                "event_id": event_id,
                "variant": slug,
                "path": repo_relpath(out),
                "model_vs_actual": report.get("model_vs_actual"),
                "ep_next_vs_actual": report.get("ep_next_vs_actual"),
            }
        )
    return {"now": clock.isoformat(), "actions": actions}
