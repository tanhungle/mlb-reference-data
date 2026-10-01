# MLB Reference Data

Public historical MLB reference data used by the (private) `sport-tracking`
tout-grading project. This is public game/odds data, not proprietary tout
picks.

| File | Description |
|---|---|
| `2021teamstats.csv` ... `2025teamstats.csv` | Team-level box score stats per season (batting/pitching/fielding, one row per team per game) |
| `games_all.csv` | Historical MLB games, grouped into series (4+ years) |
| `games_all_series_report.csv` | Series-level rollups (Game 1 -> Game 2 continuation, sweep rates, day-of-week splits) |
| `odds_flat.csv` | Historical moneyline/spread/totals odds (regular season only -- its October rows are the last regular-season days) |
| `mlb_postseason_games.csv` | One row per postseason game, 2021-2025 (208 games, 53 series): round, series id/game number, best-of, pre-game series state (each team's wins, elimination/clinch flags), higher seed, regular-season records, final/F5/1st-inning scores, series winner, and closing moneyline/total columns (filled for 2021-2022, blank for 2023-2025 until a source is found). Built by `scripts/build_postseason_games.py`; kept separate so playoff games never mix into the regular-season tables |
| `mlb_postseason_odds.csv` | Closing lines per postseason game, keyed by Retrosheet `gid`. Currently 77 games (all of 2021-2022) from ESPN's archived consensus line; ESPN keeps no lines for 2023-2025 postseason games, so those are absent rather than estimated. Fetched by sport-tracking's `fetch_mlb_postseason_odds.py`; merged into `mlb_postseason_games.csv` when present, otherwise those columns stay blank |
