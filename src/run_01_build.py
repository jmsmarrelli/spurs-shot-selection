"""Stage 1 - one shot profile per team per season, and the league's own path.

    python src/run_01_build.py

The unit of analysis is a team-season's mix of five shot zones. That is a
deliberately coarse description, and coarse is what makes it usable across
twenty-two years: the NBA's action-type vocabulary was rewritten between 2007 and
2009 and its shot coordinates were recorded differently before 2010-11, but
"restricted area" has meant the same thing throughout.

Writes data/processed/team_seasons.csv, output/league_path.csv and
output/league_zone_value.csv.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MIN_FGA, OUT, PROC, RAW, SEASONS  # noqa: E402
import features  # noqa: E402

ZONES = ["Restricted Area", "In The Paint (Non-RA)", "Mid-Range",
         "Corner 3", "Above the Break 3"]
SHARE = [f"share_{z}" for z in ZONES]


def zone5(zone: pd.Series) -> pd.Categorical:
    z = zone.astype(str).replace({"Left Corner 3": "Corner 3", "Right Corner 3": "Corner 3"})
    return pd.Categorical(z, categories=ZONES, ordered=True)


def main() -> None:
    rows, league_rows = [], []
    zone_made = pd.Series(0.0, index=ZONES)
    zone_att = pd.Series(0.0, index=ZONES)

    for season in SEASONS:
        path = RAW / f"NBA_{season}_Shots.csv"
        if not path.exists():
            print(f"  missing {path.name} - skipping", file=sys.stderr)
            continue
        t0 = time.time()
        raw = pd.read_csv(path, low_memory=False)
        tidy = features.build(raw)
        tidy = tidy.loc[~tidy["excluded"]].copy()
        tidy["zone5"] = zone5(tidy["zone"])
        tidy["team"] = tidy["team_abbrev"].astype(str)

        counts = (tidy.groupby(["team", "zone5"], observed=False).size()
                  .unstack("zone5").reindex(columns=ZONES).fillna(0))
        shares = counts.div(counts.sum(axis=1), axis=0)
        shares.columns = SHARE
        made = tidy.groupby("team")["made"].mean()
        pps = tidy.groupby("team")["points"].mean()
        three = tidy.groupby("team")["is_three"].mean()

        tab = shares.join(pd.DataFrame({"fga": counts.sum(axis=1), "fg": made,
                                        "pps": pps, "three_rate": three}))
        tab.insert(0, "season", season)
        rows.append(tab.reset_index())

        lg = counts.sum(axis=0)
        league_rows.append({"season": season, "fga": float(lg.sum()),
                            **{f"share_{z}": lg[z] / lg.sum() for z in ZONES},
                            "pps": tidy["points"].mean(),
                            "three_rate": tidy["is_three"].mean()})

        zone_made = zone_made.add(tidy.groupby("zone5", observed=False)["made"].sum(),
                                  fill_value=0)
        zone_att = zone_att.add(tidy.groupby("zone5", observed=False).size(), fill_value=0)
        print(f"  {season}  {counts.shape[0]} teams  {int(lg.sum()):,} shots  "
              f"({time.time() - t0:.1f}s)")

    if not rows:
        raise SystemExit("No raw season files found. See data/README.md.")

    teams = pd.concat(rows, ignore_index=True)
    dropped = int((teams["fga"] < MIN_FGA).sum())
    teams = teams[teams["fga"] >= MIN_FGA]

    league = pd.DataFrame(league_rows)
    value = pd.DataFrame({
        "zone5": ZONES,
        "fga": zone_att.reindex(ZONES).to_numpy(),
        "fg": (zone_made / zone_att).reindex(ZONES).to_numpy()})
    value["pps"] = value["fg"] * np.where(
        value["zone5"].isin(["Corner 3", "Above the Break 3"]), 3.0, 2.0)

    # Shot profile value: what a team's mix would be worth at league-average
    # conversion in every zone. Movement in this number is shot selection and
    # nothing else.
    w = value.set_index("zone5")["pps"].reindex(ZONES).to_numpy()
    teams["profile_value"] = teams[SHARE].to_numpy() @ w
    league["profile_value"] = league[SHARE].to_numpy() @ w

    teams.round(6).to_csv(PROC / "team_seasons.csv", index=False)
    league.round(6).to_csv(OUT / "league_path.csv", index=False)
    value.round(6).to_csv(OUT / "league_zone_value.csv", index=False)

    print(f"\n{len(teams):,} team-seasons, {teams.season.min()}-{teams.season.max()}"
          f"  ({dropped} dropped below {MIN_FGA:,} attempts)")
    print("\nleague shot mix, first and last season")
    print(league[["season"] + SHARE + ["profile_value"]]
          .iloc[[0, -1]].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
