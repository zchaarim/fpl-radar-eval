from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def first_kickoff(fixtures: list[dict[str, Any]], event_id: int) -> datetime | None:
    times = []
    for fixture in fixtures:
        if int(fixture.get("event") or 0) != int(event_id):
            continue
        stamp = parse_utc(fixture.get("kickoff_time"))
        if stamp is not None:
            times.append(stamp)
    return min(times) if times else None


def bonus_added(event_status: dict[str, Any], event_id: int) -> bool:
    for row in event_status.get("status") or []:
        if int(row.get("event") or 0) == int(event_id) and row.get("bonus_added"):
            return True
    return False


def next_unfinished_event_id(bootstrap: dict[str, Any]) -> int:
    for event in bootstrap.get("events") or []:
        if not event.get("finished"):
            return int(event["id"])
    events = bootstrap.get("events") or []
    if not events:
        raise ValueError("bootstrap has no events")
    return int(events[-1]["id"])


def latest_finished_event_id(bootstrap: dict[str, Any]) -> int:
    finished = [int(event["id"]) for event in bootstrap.get("events") or [] if event.get("finished")]
    if not finished:
        raise ValueError("no finished gameweeks yet")
    return max(finished)
