from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fpl_radar_eval.io import REPORT_DIR, ROOT, SCORED_DIR, SNAPSHOT_DIR, read_jsonl, write_json

_SCORED_NAME = re.compile(r"^gw(\d+)(?:\.(.+))?$")
_SNAP_META = re.compile(r"^gw(\d+)(?:\.(.+))?\.meta$")


def parse_scored_stem(stem: str) -> tuple[int, str] | None:
    match = _SCORED_NAME.match(stem)
    if not match:
        return None
    return int(match.group(1)), match.group(2) or "default"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_scored(root: Path = ROOT) -> list[dict[str, Any]]:
    scored_dir = root / "data" / "scored" if root != ROOT else SCORED_DIR
    rows: list[dict[str, Any]] = []
    for path in sorted(scored_dir.glob("gw*.json")):
        parsed = parse_scored_stem(path.stem)
        if parsed is None:
            continue
        event_id, variant = parsed
        payload = _load_json(path)
        model = payload.get("model_vs_actual") or {}
        ep = payload.get("ep_next_vs_actual") or {}
        rows.append(
            {
                "event_id": int(payload.get("event_id") or event_id),
                "variant": variant,
                "late": bool(payload.get("late")),
                "players": int(payload.get("players") or model.get("n") or 0),
                "model_mae": float(model.get("mae") or 0.0),
                "model_bias": float(model.get("bias") or 0.0),
                "ep_mae": float(ep.get("mae") or 0.0),
                "ep_bias": float(ep.get("bias") or 0.0),
                "n": int(model.get("n") or payload.get("players") or 0),
                "by_position": payload.get("by_position") or {},
                "ep_next_by_position": payload.get("ep_next_by_position") or {},
                "by_component": payload.get("by_component") or {},
                "path": str(path),
            }
        )
    return rows


def load_snapshot_metas(root: Path = ROOT) -> list[dict[str, Any]]:
    snap_dir = root / "data" / "snapshots" if root != ROOT else SNAPSHOT_DIR
    rows: list[dict[str, Any]] = []
    for path in sorted(snap_dir.glob("gw*.meta.json")):
        stem = path.name.removesuffix(".json")
        match = _SNAP_META.match(stem)
        payload = _load_json(path)
        event_id = int(payload.get("event_id") or (match.group(1) if match else 0))
        variant = str(payload.get("variant") or (match.group(2) if match and match.group(2) else "default"))
        rows.append(
            {
                "event_id": event_id,
                "variant": variant,
                "late": bool(payload.get("late")),
                "players": int(payload.get("players") or 0),
                "taken_at": payload.get("taken_at"),
                "deadline_time": payload.get("deadline_time"),
                "first_kickoff": payload.get("first_kickoff"),
                "replaced": payload.get("replaced"),
                "placeholder": bool(payload.get("placeholder")),
                "path": str(path),
            }
        )
    return rows


def pool_mae_bias(rows: list[dict[str, Any]], mae_key: str, bias_key: str) -> dict[str, float]:
    weight = sum(int(row.get("n") or 0) for row in rows)
    if weight <= 0:
        return {"n": 0, "mae": 0.0, "bias": 0.0}
    mae = sum(float(row[mae_key]) * int(row["n"]) for row in rows) / weight
    bias = sum(float(row[bias_key]) * int(row["n"]) for row in rows) / weight
    return {"n": weight, "mae": round(mae, 4), "bias": round(bias, 4)}


def disagreement_rows(root: Path = ROOT, event_id: int | None = None, limit: int = 15) -> list[dict[str, Any]]:
    snap_dir = root / "data" / "snapshots" if root != ROOT else SNAPSHOT_DIR
    if event_id is None:
        metas = [row for row in load_snapshot_metas(root) if row["variant"] == "default"]
        if not metas:
            return []
        event_id = max(int(row["event_id"]) for row in metas)
    path = snap_dir / f"gw{int(event_id)}.jsonl"
    if not path.exists():
        return []
    ranked: list[dict[str, Any]] = []
    for row in read_jsonl(path):
        ep = row.get("ep_next")
        if ep is None:
            continue
        pred = float(row.get("predicted") or 0.0)
        epf = float(ep)
        ranked.append(
            {
                "event_id": int(row.get("event_id") or event_id),
                "web_name": row.get("web_name"),
                "position": row.get("position"),
                "predicted": round(pred, 2),
                "ep_next": round(epf, 2),
                "gap": round(pred - epf, 2),
                "abs_gap": round(abs(pred - epf), 2),
                "rate_source": row.get("rate_source"),
            }
        )
    ranked.sort(key=lambda item: item["abs_gap"], reverse=True)
    return ranked[: max(int(limit), 0)]


def build_board(root: Path = ROOT) -> dict[str, Any]:
    scored = load_scored(root)
    metas = load_snapshot_metas(root)
    default_scores = [row for row in scored if row["variant"] == "default"]
    clean = [row for row in default_scores if not row["late"]]
    late = [row for row in default_scores if row["late"]]
    latest_snap = None
    default_metas = [row for row in metas if row["variant"] == "default"]
    if default_metas:
        latest_snap = max(default_metas, key=lambda row: int(row["event_id"]))
    latest_id = int(latest_snap["event_id"]) if latest_snap else None
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scored": scored,
        "snapshot_metas": metas,
        "default_scores": default_scores,
        "clean_scores": clean,
        "late_scores": late,
        "pooled_clean": pool_mae_bias(clean, "model_mae", "model_bias"),
        "pooled_clean_ep": pool_mae_bias(clean, "ep_mae", "ep_bias"),
        "pooled_all_default": pool_mae_bias(default_scores, "model_mae", "model_bias"),
        "disagreement": disagreement_rows(root, latest_id),
        "latest_snapshot": latest_snap,
    }


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([line, sep, *body]) if rows else "_None yet._"


def render_markdown(board: dict[str, Any]) -> str:
    clean = board["clean_scores"]
    late = board["late_scores"]
    pooled = board["pooled_clean"]
    pooled_ep = board["pooled_clean_ep"]
    latest = board.get("latest_snapshot") or {}
    lines = [
        "# FPL Radar eval report",
        "",
        f"Generated `{board['generated_at']}` from `data/scored/` and `data/snapshots/`.",
        "Tick regenerates this file. Prospective totals **exclude** `late: true` weeks.",
        "",
        "## Season (clean GWs only)",
        "",
    ]
    if clean:
        lines += [
            _md_table(
                ["series", "player-GWs", "MAE", "bias"],
                [
                    ["model", pooled["n"], pooled["mae"], pooled["bias"]],
                    ["FPL ep_next", pooled_ep["n"], pooled_ep["mae"], pooled_ep["bias"]],
                ],
            ),
            "",
            "Pooled MAE is the n-weighted mean of per-GW MAEs (same as stacking every player-GW row).",
            "",
        ]
    else:
        lines += ["No clean (`late: false`) scored gameweeks yet.", ""]

    lines += ["## Per gameweek (default variant)", ""]
    gw_rows = []
    for row in sorted(board["default_scores"], key=lambda item: item["event_id"]):
        gw_rows.append(
            [
                row["event_id"],
                "late" if row["late"] else "clean",
                row["n"],
                row["model_mae"],
                row["model_bias"],
                row["ep_mae"],
                row["ep_bias"],
            ]
        )
    lines += [
        _md_table(
            ["GW", "flag", "n", "model MAE", "model bias", "ep_next MAE", "ep_next bias"],
            gw_rows,
        )
        if gw_rows
        else "_No scored files._",
        "",
    ]

    if late:
        lines += [
            f"Late scored GWs (kept in the table, dropped from season totals): "
            f"{', '.join(str(row['event_id']) for row in late)}.",
            "",
        ]

    lines += ["## Shrinkage variants vs default (scored)", ""]
    by_gw: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in board["scored"]:
        by_gw[int(row["event_id"])].append(row)
    for event_id in sorted(by_gw):
        chunk = sorted(by_gw[event_id], key=lambda item: (item["model_mae"], item["variant"]))
        default = next((item for item in chunk if item["variant"] == "default"), None)
        lines.append(f"### GW{event_id}")
        lines.append("")
        table = []
        for item in chunk:
            delta = ""
            if default and item["variant"] != "default":
                delta = f"{item['model_mae'] - default['model_mae']:+.4f}"
            table.append(
                [
                    item["variant"],
                    "late" if item["late"] else "clean",
                    item["model_mae"],
                    item["model_bias"],
                    delta or "—",
                ]
            )
        lines += [_md_table(["variant", "flag", "MAE", "bias", "Δ MAE vs default"], table), ""]

    if clean or late:
        lines += ["## Latest scored components (default)", ""]
        sample = max(board["default_scores"], key=lambda item: item["event_id"])
        lines.append(f"GW{sample['event_id']} ({'late' if sample['late'] else 'clean'}).")
        lines.append("")
        comp_rows = [
            [key, stats.get("mae"), stats.get("bias")]
            for key, stats in (sample.get("by_component") or {}).items()
        ]
        pos_rows = []
        for pos, stats in (sample.get("by_position") or {}).items():
            ep_pos = (sample.get("ep_next_by_position") or {}).get(pos) or {}
            pos_rows.append(
                [pos, stats.get("n"), stats.get("mae"), stats.get("bias"), ep_pos.get("mae"), ep_pos.get("bias")]
            )
        lines += [
            _md_table(["component", "MAE", "bias"], comp_rows),
            "",
            _md_table(["pos", "n", "model MAE", "model bias", "ep MAE", "ep bias"], pos_rows),
            "",
        ]

    lines += ["## Snapshots on disk", ""]
    snap_rows = [
        [
            row["event_id"],
            row["variant"],
            "late" if row["late"] else "ok",
            row["players"],
            row.get("taken_at") or "",
            row.get("first_kickoff") or "",
        ]
        for row in board["snapshot_metas"]
    ]
    lines += [
        _md_table(["GW", "variant", "flag", "n", "taken_at", "first_kickoff"], snap_rows)
        if snap_rows
        else "_No snapshot metas._",
        "",
    ]

    if latest:
        lines += [
            f"## Model vs FPL `ep_next` on latest snapshot (GW{latest['event_id']})",
            "",
            "No live scores required. Gap = predicted − ep_next.",
            "",
        ]
        disagree = board.get("disagreement") or []
        lines += [
            _md_table(
                ["player", "pos", "xP", "ep_next", "gap"],
                [
                    [row["web_name"], row["position"], row["predicted"], row["ep_next"], row["gap"]]
                    for row in disagree
                ],
            )
            if disagree
            else "_No snapshot jsonl._",
            "",
        ]

    lines += [
        "## How to read this",
        "",
        "- **Clean season totals** are the numbers to use when changing fpl-radar-backend.",
        "- Promote a k-variant only if Δ MAE vs default is better for two clean GWs.",
        "- Large positive gap (us >> FPL): availability / flags we still ignore.",
        "- Large negative gap (FPL >> us): minutes or haul FPL is pricing and we shrink away.",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_report(root: Path = ROOT) -> Path:
    board = build_board(root)
    report_dir = root / "data" / "reports" if root != ROOT else REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = report_dir / "eval.md"
    markdown_path.write_text(render_markdown(board), encoding="utf-8")
    write_json(
        report_dir / "eval.summary.json",
        {
            "generated_at": board["generated_at"],
            "clean_gws": [row["event_id"] for row in board["clean_scores"]],
            "late_gws": [row["event_id"] for row in board["late_scores"]],
            "pooled_clean": board["pooled_clean"],
            "pooled_clean_ep": board["pooled_clean_ep"],
            "latest_snapshot": board.get("latest_snapshot"),
        },
    )
    return markdown_path
