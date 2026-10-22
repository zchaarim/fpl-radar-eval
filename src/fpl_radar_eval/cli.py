from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fpl_radar.fpl_rules import add_shrinkage_arguments, shrinkage_from_args

from fpl_radar_eval.io import repo_relpath, scored_path, snapshot_path, write_json, write_jsonl
from fpl_radar_eval.report import write_report
from fpl_radar_eval.score import run_score
from fpl_radar_eval.snapshot import build_snapshot_rows
from fpl_radar_eval.tick import run_tick


def cmd_snapshot(args: argparse.Namespace) -> int:
    shrinkage = shrinkage_from_args(args)
    rows, meta = build_snapshot_rows(
        int(args.event or 0),
        sync=bool(args.sync),
        shrinkage=shrinkage,
    )
    event_id = int(meta["event_id"])
    variant = str(meta.get("variant") or "default")
    out = snapshot_path(event_id, Path(args.out) if args.out else None, variant=variant)
    n = write_jsonl(out, rows)
    write_json(out.with_suffix(".meta.json"), {**meta, "wrote": n, "path": repo_relpath(out)})
    print(json.dumps({**meta, "wrote": n, "path": repo_relpath(out)}, default=str))
    return 0


def _print_score(report: dict) -> None:
    print(
        f"GW {report['event_id']}  n={report['players']}  "
        f"model MAE {report['model_vs_actual']['mae']}  "
        f"bias {report['model_vs_actual']['bias']}  "
        f"ep_next MAE {report['ep_next_vs_actual']['mae']}"
    )
    print("By position (model):")
    for pos, stats in report["by_position"].items():
        print(f"  {pos:3}  n={stats['n']:4}  MAE {stats['mae']:6.3f}  bias {stats['bias']:+7.3f}")
    print("By component (model, non-placeholder):")
    for key, stats in report["by_component"].items():
        print(f"  {key:8}  MAE {stats['mae']:6.3f}  bias {stats['bias']:+7.3f}")


def cmd_score(args: argparse.Namespace) -> int:
    snap = Path(args.snapshot) if args.snapshot else None
    variant = args.variant or "default"
    report = run_score(args.event, snap, variant=variant)
    event_id = int(report["event_id"])
    out = scored_path(event_id, Path(args.out) if args.out else None, variant=variant)
    payload = {k: v for k, v in report.items() if k != "rows"}
    if "snapshot" in payload:
        payload["snapshot"] = repo_relpath(Path(str(payload["snapshot"])))
    if args.keep_rows:
        payload["rows"] = report["rows"]
    write_json(out, payload)
    _print_score(report)
    print(f"Wrote {out}")
    return 0


def cmd_tick(args: argparse.Namespace) -> int:
    report = run_tick(sync=not args.no_sync, dry_run=bool(args.dry_run))
    print(json.dumps(report, default=str, indent=2))
    return 0


def cmd_report(_args: argparse.Namespace) -> int:
    path, wrote = write_report()
    print(f"Wrote {path}" if wrote else f"Unchanged {path} (snapshot/score data matches last report)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fpl-radar-eval")
    sub = parser.add_subparsers(dest="command", required=True)

    snap = sub.add_parser("snapshot", help="Freeze horizon-1 xP for a gameweek (before it is played)")
    snap.add_argument("--event", type=int, default=None, help="Gameweek id (default: next unfinished)")
    snap.add_argument("--sync", action="store_true", help="Refresh FPL + Understat caches first")
    snap.add_argument("--out", default=None, help="jsonl path (default data/snapshots/gwN.jsonl)")
    add_shrinkage_arguments(snap)
    snap.set_defaults(func=cmd_snapshot)

    score = sub.add_parser("score", help="Compare a snapshot to FPL live stats after the GW")
    score.add_argument("--event", type=int, default=None, help="Gameweek id (default: latest finished)")
    score.add_argument("--snapshot", default=None, help="jsonl from snapshot")
    score.add_argument("--variant", default="default", help="Matches snapshot slug, e.g. minutes-k-2")
    score.add_argument("--out", default=None, help="summary JSON (default data/scored/gwN.json)")
    score.add_argument("--keep-rows", action="store_true", help="Include per-player rows in the JSON")
    score.set_defaults(func=cmd_score)

    tick = sub.add_parser(
        "tick",
        help="If FPL deadline has passed, snapshot; if the GW is finished and bonus is in, score",
    )
    tick.add_argument("--no-sync", action="store_true", help="Use caches only")
    tick.add_argument("--dry-run", action="store_true", help="Print decisions without writing")
    tick.set_defaults(func=cmd_tick)

    report = sub.add_parser("report", help="Rebuild data/reports/eval.md from snapshots and scores")
    report.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
