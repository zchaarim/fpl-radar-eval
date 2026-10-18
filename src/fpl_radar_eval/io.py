from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
SCORED_DIR = ROOT / "data" / "scored"


def repo_relpath(path: Path) -> str:
    """Repo-relative posix path for committed JSON (no home-directory leak)."""
    resolved = path.expanduser().resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def snapshot_path(
    event_id: int,
    explicit: Path | None = None,
    variant: str = "default",
) -> Path:
    if explicit is not None:
        return explicit
    if variant and variant != "default":
        return SNAPSHOT_DIR / f"gw{int(event_id)}.{variant}.jsonl"
    return SNAPSHOT_DIR / f"gw{int(event_id)}.jsonl"


def scored_path(
    event_id: int,
    explicit: Path | None = None,
    variant: str = "default",
) -> Path:
    if explicit is not None:
        return explicit
    if variant and variant != "default":
        return SCORED_DIR / f"gw{int(event_id)}.{variant}.json"
    return SCORED_DIR / f"gw{int(event_id)}.json"


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")
            count += 1
    return count


def read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
