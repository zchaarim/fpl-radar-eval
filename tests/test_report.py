from pathlib import Path

from fpl_radar_eval.report import build_board, parse_scored_stem, pool_mae_bias, render_markdown, write_report


def test_parse_scored_stem() -> None:
    assert parse_scored_stem("gw7") == (7, "default")
    assert parse_scored_stem("gw8.minutes-k-2") == (8, "minutes-k-2")
    assert parse_scored_stem("not-a-score") is None


def test_pool_mae_bias_is_n_weighted() -> None:
    pooled = pool_mae_bias(
        [
            {"n": 2, "model_mae": 1.0, "model_bias": 0.0},
            {"n": 8, "model_mae": 2.0, "model_bias": 1.0},
        ],
        "model_mae",
        "model_bias",
    )
    assert pooled["n"] == 10
    assert pooled["mae"] == 1.8
    assert pooled["bias"] == 0.8


def test_write_report_excludes_late_from_season(tmp_path: Path) -> None:
    scored = tmp_path / "data" / "scored"
    snaps = tmp_path / "data" / "snapshots"
    scored.mkdir(parents=True)
    snaps.mkdir(parents=True)
    (scored / "gw7.json").write_text(
        '{"event_id":7,"players":10,"late":true,'
        '"model_vs_actual":{"n":10,"mae":1.5,"bias":0.1},'
        '"ep_next_vs_actual":{"n":10,"mae":1.0,"bias":0.2},'
        '"by_position":{},"ep_next_by_position":{},"by_component":{}}\n',
        encoding="utf-8",
    )
    (scored / "gw8.json").write_text(
        '{"event_id":8,"players":10,"late":false,'
        '"model_vs_actual":{"n":10,"mae":0.5,"bias":-0.1},'
        '"ep_next_vs_actual":{"n":10,"mae":0.8,"bias":0.0},'
        '"by_position":{"MID":{"n":10,"mae":0.5,"bias":-0.1}},'
        '"ep_next_by_position":{"MID":{"n":10,"mae":0.8,"bias":0.0}},'
        '"by_component":{"attack":{"n":10,"mae":0.2,"bias":0.0}}}\n',
        encoding="utf-8",
    )
    (snaps / "gw8.meta.json").write_text(
        '{"event_id":8,"variant":"default","late":false,"players":10,'
        '"taken_at":"2026-10-22T10:40:00+00:00"}\n',
        encoding="utf-8",
    )
    (snaps / "gw8.jsonl").write_text(
        '{"player_id":1,"web_name":"Saka","position":"MID","predicted":5.0,"ep_next":1.2}\n',
        encoding="utf-8",
    )
    path, wrote = write_report(tmp_path)
    assert wrote is True
    text = path.read_text(encoding="utf-8")
    board = build_board(tmp_path)
    assert board["pooled_clean"]["mae"] == 0.5
    assert board["pooled_clean"]["n"] == 10
    assert "late" in text
    assert "Saka" in text
    assert "Generated `" not in text
    assert render_markdown(board).startswith("# FPL Radar eval report")
    first_mtime = path.stat().st_mtime_ns
    _, wrote_again = write_report(tmp_path)
    assert wrote_again is False
    assert path.stat().st_mtime_ns == first_mtime
    (snaps / "gw8.jsonl").write_text(
        '{"player_id":1,"web_name":"Saka","position":"MID","predicted":5.1,"ep_next":1.2}\n',
        encoding="utf-8",
    )
    _, wrote_new = write_report(tmp_path)
    assert wrote_new is True
