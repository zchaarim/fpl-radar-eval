# FPL Radar eval report

Built from `data/scored/` and `data/snapshots/`. Prospective totals **exclude** `late: true` weeks.

## Season (clean GWs only)

No clean (`late: false`) scored gameweeks yet.

## Per gameweek (default variant)

| GW | flag | n | model MAE | model bias | ep_next MAE | ep_next bias |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | late | 667 | 1.1397 | 0.0021 | 1.0091 | 0.2292 |

Late scored GWs (kept in the table, dropped from season totals): 7.

## Shrinkage variants vs default (scored)

### GW7

| variant | flag | MAE | bias | Δ MAE vs default |
| --- | --- | --- | --- | --- |
| minutes-k-2 | late | 1.1368 | -0.0005 | -0.0029 |
| xgi-k-4 | late | 1.1368 | 0.0006 | -0.0029 |
| team-k-20 | late | 1.138 | 0.0052 | -0.0017 |
| default | late | 1.1397 | 0.0021 | — |
| team-k-5 | late | 1.1425 | -0.0023 | +0.0028 |
| xgi-k-16 | late | 1.1427 | 0.0033 | +0.0030 |
| minutes-k-8 | late | 1.1453 | 0.0062 | +0.0056 |

## Latest scored components (default)

GW7 (late).

| component | MAE | bias |
| --- | --- | --- |
| minutes | 0.3649 | -0.0317 |
| attack | 0.4651 | -0.0293 |
| cs | 0.3045 | 0.0278 |
| gc | 0.0873 | 0.0114 |
| defcon | 0.1419 | -0.0084 |
| bonus | 0.1237 | 0.0668 |
| saves | 0.0185 | -0.0074 |
| cards | 0.1261 | -0.0272 |

| pos | n | model MAE | model bias | ep MAE | ep bias |
| --- | --- | --- | --- | --- | --- |
| GKP | 73 | 0.6008 | 0.0571 | 0.6726 | 0.2315 |
| DEF | 217 | 1.2815 | -0.0343 | 1.2 | 0.2968 |
| MID | 298 | 1.1821 | -0.0296 | 0.952 | 0.1426 |
| FWD | 79 | 1.0879 | 0.1704 | 1.0114 | 0.3684 |

## Snapshots on disk

| GW | variant | flag | n | taken_at | first_kickoff |
| --- | --- | --- | --- | --- | --- |
| 7 | default | late | 667 | 2026-10-18T09:04:13.134547+00:00 |  |
| 7 | minutes-k-2 | late | 667 | 2026-10-18T11:25:04.586852+00:00 | 2026-10-17T11:30:00+00:00 |
| 7 | minutes-k-2_xgi-k-16 | late | 667 | 2026-10-18T10:40:21.790180+00:00 |  |
| 7 | minutes-k-8 | late | 667 | 2026-10-18T11:25:06.557593+00:00 | 2026-10-17T11:30:00+00:00 |
| 7 | team-k-20 | late | 667 | 2026-10-18T11:25:14.410799+00:00 | 2026-10-17T11:30:00+00:00 |
| 7 | team-k-5 | late | 667 | 2026-10-18T11:25:12.454894+00:00 | 2026-10-17T11:30:00+00:00 |
| 7 | xgi-k-16 | late | 667 | 2026-10-18T11:25:10.492137+00:00 | 2026-10-17T11:30:00+00:00 |
| 7 | xgi-k-4 | late | 667 | 2026-10-18T11:25:08.514298+00:00 | 2026-10-17T11:30:00+00:00 |
| 8 | default | ok | 668 | 2026-10-23T12:51:09.788294+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | minutes-k-2 | ok | 668 | 2026-10-23T12:51:11.859309+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | minutes-k-8 | ok | 668 | 2026-10-23T12:51:13.958766+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | team-k-20 | ok | 668 | 2026-10-23T12:51:22.375421+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | team-k-5 | ok | 668 | 2026-10-23T12:51:20.283435+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | xgi-k-16 | ok | 668 | 2026-10-23T12:51:18.164262+00:00 | 2026-10-23T19:00:00+00:00 |
| 8 | xgi-k-4 | ok | 668 | 2026-10-23T12:51:16.073751+00:00 | 2026-10-23T19:00:00+00:00 |

## Model vs FPL `ep_next` on latest snapshot (GW8)

No live scores required. Gap = predicted − ep_next.

| player | pos | xP | ep_next | gap |
| --- | --- | --- | --- | --- |
| Henderson | MID | 1.25 | 10.5 | -9.25 |
| Doku | MID | 0.88 | 9.0 | -8.12 |
| Neto | MID | 3.83 | 10.0 | -6.17 |
| Evanilson | FWD | 3.52 | 9.5 | -5.98 |
| De Cuyper | DEF | 4.56 | 10.5 | -5.94 |
| Cherif | FWD | 0.89 | 6.5 | -5.61 |
| Ayari | MID | 2.55 | 8.0 | -5.45 |
| Vuskovic | DEF | 4.6 | 9.5 | -4.9 |
| Ouattara | DEF | 1.71 | 6.5 | -4.79 |
| Bruno G. | MID | 1.44 | 6.0 | -4.56 |
| Rice | MID | 3.55 | 8.0 | -4.45 |
| F.Kadıoğlu | DEF | 3.05 | 7.5 | -4.45 |
| Boscagli | DEF | 3.06 | 7.5 | -4.44 |
| Manzambi | MID | 1.64 | 6.0 | -4.36 |
| B.Fernandes | MID | 5.32 | 1.0 | 4.32 |

## How to read this

- **Clean season totals** are the numbers to use when changing fpl-radar-backend.
- Promote a k-variant only if Δ MAE vs default is better for two clean GWs.
- Large positive gap (us >> FPL): availability / flags we still ignore.
- Large negative gap (FPL >> us): minutes or haul FPL is pricing and we shrink away.
