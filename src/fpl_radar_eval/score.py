from __future__ import annotations

from collections import defaultdict
from typing import Any

from fpl_radar.clients.fpl import FplClient
from fpl_radar.fpl_rules import POSITION_LABELS, POSITION_ORDER, scoring_table
from fpl_radar.ingest.sync import default_cache, load_model_context

from fpl_radar_eval.components import COMPONENT_KEYS, actual_components, component_sum, other_points
from fpl_radar_eval.events import latest_finished_event_id
from fpl_radar_eval.io import read_jsonl, repo_relpath, snapshot_path


def _mae(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(abs(v) for v in values) / len(values)


def _bias(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _live_by_player(client: FplClient, event_id: int) -> dict[int, dict[str, Any]]:
    live = client.event_live(event_id)
    out: dict[int, dict[str, Any]] = {}
    for element in live.get("elements") or []:
        out[int(element["id"])] = element.get("stats") or {}
    return out


def score_snapshot(
    event_id: int,
    snapshot_rows: list[dict[str, Any]],
    live_by_player: dict[int, dict[str, Any]],
    table: dict[str, int | float],
) -> dict[str, Any]:
    joined: list[dict[str, Any]] = []
    errors_total: list[float] = []
    errors_ep: list[float] = []
    by_pos_total: dict[int, list[float]] = defaultdict(list)
    by_pos_ep: dict[int, list[float]] = defaultdict(list)
    by_comp: dict[str, list[float]] = {key: [] for key in COMPONENT_KEYS}

    for row in snapshot_rows:
        pid = int(row["player_id"])
        etype = int(row["element_type"])
        stats = live_by_player.get(pid) or {}
        actual = actual_components(stats, etype, table)
        modelled = component_sum(actual)
        other = other_points(stats, table)
        fpl_total = float(stats.get("total_points") or 0)
        predicted = float(row.get("predicted") or 0.0)
        pred_parts = row.get("predicted_components") or {}
        err = modelled - predicted
        errors_total.append(err)
        by_pos_total[etype].append(err)
        ep_next = row.get("ep_next")
        if ep_next is not None:
            ep_err = modelled - float(ep_next)
            errors_ep.append(ep_err)
            by_pos_ep[etype].append(ep_err)
        if not row.get("placeholder"):
            for key in COMPONENT_KEYS:
                by_comp[key].append(float(actual.get(key) or 0.0) - float(pred_parts.get(key) or 0.0))
        joined.append(
            {
                "player_id": pid,
                "web_name": row.get("web_name"),
                "position": row.get("position") or POSITION_LABELS.get(etype),
                "predicted": predicted,
                "actual_modelled": modelled,
                "actual_fpl_total": fpl_total,
                "other_points": other,
                "error": err,
                "ep_next": ep_next,
            }
        )

    def pack(errs: list[float]) -> dict[str, float]:
        return {"n": len(errs), "mae": round(_mae(errs), 4), "bias": round(_bias(errs), 4)}

    return {
        "event_id": event_id,
        "players": len(joined),
        "model_vs_actual": pack(errors_total),
        "ep_next_vs_actual": pack(errors_ep),
        "by_position": {
            POSITION_LABELS.get(etype, str(etype)): pack(by_pos_total.get(etype, []))
            for etype in POSITION_ORDER
        },
        "ep_next_by_position": {
            POSITION_LABELS.get(etype, str(etype)): pack(by_pos_ep.get(etype, []))
            for etype in POSITION_ORDER
        },
        "by_component": {key: pack(by_comp[key]) for key in COMPONENT_KEYS},
        "rows": joined,
    }


def run_score(
    event_id: int | None = None,
    snapshot_file: Any = None,
    variant: str = "default",
) -> dict[str, Any]:
    client = FplClient(cache=default_cache())
    ctx = load_model_context(client)
    if event_id is None or event_id <= 0:
        event_id = latest_finished_event_id(ctx.bootstrap)
    path = snapshot_path(event_id, snapshot_file, variant=variant)
    if not path.exists():
        raise FileNotFoundError(
            f"No snapshot at {path}. Run `python -m fpl_radar_eval snapshot --event {event_id}` "
            "before the gameweek is played."
        )
    rows = list(read_jsonl(path))
    table = scoring_table(ctx.bootstrap.get("game_settings"))
    live = _live_by_player(client, event_id)
    report = score_snapshot(event_id, rows, live, table)
    report["snapshot"] = repo_relpath(path)
    report["late"] = any(bool(row.get("late")) for row in rows)
    return report
