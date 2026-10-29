# FPL Radar eval report

Built from `data/scored/` and `data/snapshots/`. Prospective totals **exclude** `late: true` weeks.

## Season (clean GWs only)

| series | player-GWs | MAE | bias |
| --- | --- | --- | --- |
| model | 668 | 1.2421 | 0.0725 |
| FPL ep_next | 668 | 1.3132 | 0.1168 |

Pooled MAE is the n-weighted mean of per-GW MAEs (same as stacking every player-GW row).

## Per gameweek (default variant)

| GW | flag | n | model MAE | model bias | ep_next MAE | ep_next bias |
| --- | --- | --- | --- | --- | --- | --- |
| 7 | late | 667 | 1.1397 | 0.0021 | 1.0091 | 0.2292 |
| 8 | clean | 668 | 1.2421 | 0.0725 | 1.3132 | 0.1168 |

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

### GW8

| variant | flag | MAE | bias | Δ MAE vs default |
| --- | --- | --- | --- | --- |
| minutes-k-2 | clean | 1.2398 | 0.0698 | -0.0023 |
| xgi-k-16 | clean | 1.2413 | 0.0737 | -0.0008 |
| team-k-5 | clean | 1.2415 | 0.0691 | -0.0006 |
| default | clean | 1.2421 | 0.0725 | — |
| team-k-20 | clean | 1.2427 | 0.0747 | +0.0006 |
| xgi-k-4 | clean | 1.2434 | 0.0711 | +0.0013 |
| minutes-k-8 | clean | 1.2467 | 0.0771 | +0.0046 |

## Latest scored components (default)

GW8 (clean).

| component | MAE | bias |
| --- | --- | --- |
| minutes | 0.4019 | -0.0146 |
| attack | 0.4045 | -0.0979 |
| cs | 0.3879 | 0.0825 |
| gc | 0.0868 | 0.0184 |
| defcon | 0.1774 | 0.031 |
| bonus | 0.1173 | 0.0558 |
| saves | 0.0202 | -0.0003 |
| cards | 0.1052 | -0.0024 |

| pos | n | model MAE | model bias | ep MAE | ep bias |
| --- | --- | --- | --- | --- | --- |
| GKP | 73 | 0.9009 | 0.2618 | 0.8082 | 0.4384 |
| DEF | 217 | 1.6082 | 0.1297 | 1.6014 | 0.3332 |
| MID | 299 | 1.1 | 0.003 | 1.2682 | -0.0375 |
| FWD | 79 | 1.0892 | 0.003 | 1.1582 | -0.1911 |

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
| 9 | default | ok | 669 | 2026-10-29T16:28:01.948880+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | minutes-k-2 | ok | 669 | 2026-10-29T16:28:03.049784+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | minutes-k-8 | ok | 669 | 2026-10-29T16:28:04.351856+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | team-k-20 | ok | 669 | 2026-10-29T16:28:08.857446+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | team-k-5 | ok | 669 | 2026-10-29T16:28:07.763383+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | xgi-k-16 | ok | 669 | 2026-10-29T16:28:06.658358+00:00 | 2026-10-31T12:30:00+00:00 |
| 9 | xgi-k-4 | ok | 669 | 2026-10-29T16:28:05.464331+00:00 | 2026-10-31T12:30:00+00:00 |

## Model vs FPL `ep_next` on latest snapshot (GW9)

No live scores required. Gap = predicted − ep_next.

| player | pos | xP | ep_next | gap |
| --- | --- | --- | --- | --- |
| Henderson | MID | 1.34 | 7.7 | -6.36 |
| Doku | MID | 1.13 | 6.7 | -5.57 |
| Konsa | DEF | 3.92 | 9.0 | -5.08 |
| N.Jackson | FWD | 3.09 | 8.0 | -4.91 |
| Evanilson | FWD | 3.5 | 8.3 | -4.8 |
| Saka | MID | 4.23 | 0.0 | 4.23 |
| De Cuyper | DEF | 3.16 | 7.3 | -4.14 |
| Neto | MID | 3.68 | 7.7 | -4.02 |
| Cherif | FWD | 1.03 | 5.0 | -3.97 |
| João Pedro | FWD | 3.85 | 0.0 | 3.85 |
| Ayari | MID | 2.31 | 6.0 | -3.69 |
| Gabriel | DEF | 5.37 | 9.0 | -3.63 |
| Hato | DEF | 2.25 | 5.7 | -3.45 |
| Vuskovic | DEF | 3.33 | 6.7 | -3.37 |
| Ouattara | DEF | 1.7 | 5.0 | -3.3 |

## How to read this

- **Clean season totals** are the numbers to use when changing fpl-radar-backend.
- Promote a k-variant only if Δ MAE vs default is better for two clean GWs.
- Large positive gap (us >> FPL): availability / flags we still ignore.
- Large negative gap (FPL >> us): minutes or haul FPL is pricing and we shrink away.
