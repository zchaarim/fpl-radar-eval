from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

_FINGERPRINT_SKIP = frozenset({"taken_at", "late"})

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
SCORED_DIR = ROOT / "data" / "scored"
REPORT_DIR = ROOT / "data" / "reports"


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


def _fingerprint_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {str(key): _fingerprint_value(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, list):
        return [_fingerprint_value(item) for item in value]
    return value


def snapshot_fingerprint(rows: Iterable[dict[str, Any]]) -> str:
    """Hash of predictions and FPL ep_* only — ignores taken_at / late so rebuilds can match."""
    payload = []
    for row in sorted(rows, key=lambda item: int(item.get("player_id") or 0)):
        payload.append(
            {
                key: _fingerprint_value(value)
                for key, value in sorted(row.items())
                if key not in _FINGERPRINT_SKIP
            }
        )
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def snapshots_equivalent(existing: Iterable[dict[str, Any]], incoming: Iterable[dict[str, Any]]) -> bool:
    return snapshot_fingerprint(existing) == snapshot_fingerprint(incoming)
