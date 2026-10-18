from __future__ import annotations

from typing import Any

from fpl_radar.fpl_rules import ShrinkageConfig
from fpl_radar.xp.snapshot import build_snapshot


def build_snapshot_rows(
    event_id: int,
    *,
    sync: bool = False,
    late: bool = False,
    deadline_time: str | None = None,
    first_kickoff: str | None = None,
    shrinkage: ShrinkageConfig | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_snapshot(
        event_id,
        sync=sync,
        shrinkage=shrinkage,
        late=late,
        deadline_time=deadline_time,
        first_kickoff=first_kickoff,
    )
