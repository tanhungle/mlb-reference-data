"""Build mlb_postseason_games.csv: one row per MLB postseason game, 2021-2025.

Kept separate from the regular-season tables (games_all.csv,
games_all_series_report.csv, odds_flat.csv) on purpose -- those are
regular-season oriented, and mixing playoff games into them would skew
every regular-season split built on them.

Sources:
- <year>teamstats.csv (Retrosheet team-game logs): scores, innings, and
  the regular-season records used for seeding context.
- mlb_postseason_odds.csv (optional): closing lines keyed by gid. When
  absent or missing a game, the closing_* columns are left blank -- never
  guessed or filled from the regular-season odds file.

Series state columns are measured BEFORE the game is played, so they can
be used as pre-game features without leaking the result.

Usage: python3 scripts/build_postseason_games.py   (run from the repo root)
"""
import collections
import csv
import os

YEARS = range(2021, 2026)
ROUNDS = {"wildcard": "WC", "divisionseries": "DS", "lcs": "LCS", "worldseries": "WS"}
ODDS_COLUMNS = ["closing_home_ml", "closing_away_ml", "closing_total", "closing_over_odds",
                "closing_under_odds", "odds_source"]
COLUMNS = (["season", "round", "series_id", "series_game", "best_of", "date", "gid", "home", "away",
            "home_league", "away_league",
            "home_reg_w", "home_reg_l", "away_reg_w", "away_reg_l", "home_reg_wpct", "away_reg_wpct",
            "higher_seed", "home_is_higher_seed",
            "home_series_wins_before", "away_series_wins_before",
            "home_facing_elimination", "away_facing_elimination", "home_can_clinch", "away_can_clinch",
            "home_score", "away_score", "winner", "total_runs", "innings",
            "home_f5", "away_f5", "f5_winner", "home_inn1", "away_inn1",
            "series_winner"] + ODDS_COLUMNS)

AL = {"BAL", "BOS", "NYA", "TBA", "TOR", "CHA", "CLE", "DET", "KCA", "MIN", "ANA", "HOU", "OAK", "ATH", "SEA", "TEX"}


def best_of(season, rnd):
    if rnd == "WC":
        return 1 if season == 2021 else 3
    return 5 if rnd == "DS" else 7


def load_season(year):
    rec = collections.Counter()
    games = collections.defaultdict(dict)
    with open(f"{year}teamstats.csv", newline="") as f:
        for r in csv.DictReader(f):
            if r["gametype"] == "regular":
                rec[(r["team"], "w")] += int(r["win"] or 0)
                rec[(r["team"], "l")] += int(r["loss"] or 0)
            elif r["gametype"] in ROUNDS:
                games[r["gid"]][r["vishome"]] = r
    return rec, games


def innings(r):
    return [int(r[f"inn{i}"]) for i in range(1, 29) if r[f"inn{i}"] not in ("", None)]


def load_odds():
    if not os.path.exists("mlb_postseason_odds.csv"):
        return {}
    with open("mlb_postseason_odds.csv", newline="") as f:
        return {r["gid"]: r for r in csv.DictReader(f)}


def main():
    odds = load_odds()
    out = []
    for year in YEARS:
        rec, games = load_season(year)
        wpct = lambda t: rec[(t, "w")] / max(1, rec[(t, "w")] + rec[(t, "l")])
        series = collections.defaultdict(list)
        for gid, sides in games.items():
            if "h" not in sides or "v" not in sides:
                continue
            h, v = sides["h"], sides["v"]
            rnd = ROUNDS[h["gametype"]]
            series[(rnd, frozenset((h["team"], v["team"])))].append((h["date"], h["number"], gid, h, v))

        for (rnd, teams), gs in series.items():
            gs.sort()
            g1_home = gs[0][3]["team"]
            a, b = sorted(teams)
            sid = f"{year}-{rnd}-{a}-{b}"
            need = best_of(year, rnd) // 2 + 1
            wins = collections.Counter()
            rows = []
            for n, (date, _, gid, h, v) in enumerate(gs, 1):
                home, away = h["team"], v["team"]
                hs, vs = int(h["b_r"]), int(v["b_r"])
                hi, vi = innings(h), innings(v)
                h5, v5 = sum(hi[:5]), sum(vi[:5])
                row = {
                    "season": year, "round": rnd, "series_id": sid, "series_game": n,
                    "best_of": best_of(year, rnd), "date": f"{date[:4]}-{date[4:6]}-{date[6:]}", "gid": gid,
                    "home": home, "away": away,
                    "home_league": "AL" if home in AL else "NL", "away_league": "AL" if away in AL else "NL",
                    "home_reg_w": rec[(home, "w")], "home_reg_l": rec[(home, "l")],
                    "away_reg_w": rec[(away, "w")], "away_reg_l": rec[(away, "l")],
                    "home_reg_wpct": f"{wpct(home):.3f}", "away_reg_wpct": f"{wpct(away):.3f}",
                    # Game 1 is hosted by the higher seed in every round
                    # (World Series home field also goes to the better record).
                    "higher_seed": g1_home, "home_is_higher_seed": int(home == g1_home),
                    "home_series_wins_before": wins[home], "away_series_wins_before": wins[away],
                    "home_facing_elimination": int(wins[away] == need - 1),
                    "away_facing_elimination": int(wins[home] == need - 1),
                    "home_can_clinch": int(wins[home] == need - 1),
                    "away_can_clinch": int(wins[away] == need - 1),
                    "home_score": hs, "away_score": vs, "winner": home if hs > vs else away,
                    "total_runs": hs + vs, "innings": max(len(hi), len(vi)),
                    "home_f5": h5, "away_f5": v5,
                    "f5_winner": home if h5 > v5 else (away if v5 > h5 else "TIE"),
                    "home_inn1": hi[0] if hi else "", "away_inn1": vi[0] if vi else "",
                }
                o = odds.get(gid, {})
                for c in ODDS_COLUMNS:
                    row[c] = o.get(c, "")
                wins[row["winner"]] += 1
                rows.append(row)
            winner = wins.most_common(1)[0][0]
            for row in rows:
                row["series_winner"] = winner
            out.extend(rows)

    out.sort(key=lambda r: (r["date"], r["gid"]))
    with open("mlb_postseason_games.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out)
    with_odds = sum(1 for r in out if r["closing_home_ml"])
    print(f"Wrote {len(out)} games, {len({r['series_id'] for r in out})} series, {with_odds} with closing odds")


if __name__ == "__main__":
    main()
