# FPL Radar eval

Offline scoring of [fpl-radar-backend](https://github.com/zchaarim/fpl-radar-backend) expected points. Freeze a **horizon-1** prediction (and the minutes / attack / CS / GC / DefCon / bonus / saves / cards split) **before** a gameweek is played, then compare it to FPL `event/{gw}/live/` after bonus is in.

This is not the API and is not shipped in the Docker image. Calling the model *after* a GW using today’s cache leaks that week’s minutes and xGI into the “prediction.”

## Setup

Sibling of `fpl-radar-backend`. Python 3.11+.

```text
python -m pip install -e ".[dev]"
```

That pulls `fpl-radar-backend` from `../fpl-radar-backend` (see `pyproject.toml`).

Point `FPL_DATA_DIR` at the backend data directory so snapshot/score reuse the same FPL + Understat cache (and mappings):

```powershell
$env:FPL_DATA_DIR = "..\fpl-radar-backend\data"
python -m fpl_radar_eval snapshot --sync
```

## Commands

```text
python -m fpl_radar_eval snapshot [--event N] [--sync] [--minutes-k 2] [--xgi-k 16] ...
python -m fpl_radar_eval score [--event N] [--variant minutes-k-2]
python -m fpl_radar_eval tick [--dry-run] [--no-sync]
```

`tick` (and GitHub Actions) writes the production snapshot plus six one-knob variants (`minutes-k` 2/8, `xgi-k` 4/16, `team-k` 5/20). It **skips any file that already exists**. Manual `--minutes-k` etc. are only for extra experiments beyond that set.

`snapshot` defaults to the next unfinished gameweek. `score` defaults to the latest finished gameweek and reads `data/snapshots/gw{N}.jsonl`. It prints MAE / bias for modelled points vs FPL live, by position and by component, and the same totals vs FPL `ep_next` stored on the snapshot.

`ep_next` is only a fair baseline if it was written **before** that GW (it is stored on the snapshot, not read live at score time).

## Layout

- `data/snapshots/` — append-only jsonl, one row per player per GW. Safe to commit. GW7 was frozen after several fixtures had finished (`late: true`); keep it, but do not treat it as a clean pre-match prediction. The prospective series starts at the next deadline.
- `data/scored/` — summary JSON from `score`. Safe to commit.

Parameter sweeps and previous-season walk-forwards can live here later. Do not add them to the backend.

## GitHub Actions

`.github/workflows/eval.yml` runs about every 15 minutes (GitHub may delay scheduled jobs) and on **Actions → Eval tick → Run workflow**. It does **not** assume a Friday 11:00. Each run pulls FPL bootstrap + fixtures + `event-status` and:

1. **Snapshot** after `deadline_time` for an unfinished GW: any of `gwN.jsonl` / `gwN.<variant>.jsonl` that are **missing**. Existing files are left alone. If a fixture has already kicked off, new files are marked `late: true`, and tick will not add extra variants when at least one freeze already exists.
2. **Score** when that GW is `finished` and bonus is on `event-status`: any variant that **has a snapshot** and **does not** yet have `data/scored/gwN.json` (or `gwN.<variant>.json`).

New jsonl/JSON are committed back to this repo. Enable **Actions** write on the default branch. Scheduled workflows pause if the repo is inactive for 60 days; a push or a manual run wakes them.
