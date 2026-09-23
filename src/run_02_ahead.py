"""Stage 2 - was San Antonio actually early?

    python src/run_02_ahead.py

Three ways of asking it, because the answer depends on which one you mean.

1. **Volume.** Did they shoot more threes than the league? This is the version
   people usually argue about and the easiest to check.
2. **Location.** Did they shoot the *good* threes - the corner - before anyone
   else? The Bruce Bowen and Danny Green claim.
3. **The whole chart.** Which season's league average did their shot mix look
   like? That is the version that treats shot selection as one decision rather
   than five.

Writes output/years_ahead.csv, output/team_ranking.csv, output/spurs_path.csv
and figures 01-05.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (COMPARISONS, DYNASTY, EXTRAPOLATE_YEARS, FIG, OUT,  # noqa: E402
                    PROC, TEAM, TREND_WINDOW)
import ahead as A  # noqa: E402
import labels as L  # noqa: E402
import style as S  # noqa: E402

ZONES = A.ZONES
CORNER = "share_Corner 3"
MID = "share_Mid-Range"


def spread(values: dict, min_gap: float) -> dict:
    """Push end-of-line labels apart just enough that they stop colliding."""
    placed, prev = {}, -np.inf
    for k in sorted(values, key=values.get):
        y = max(values[k], prev + min_gap)
        placed[k], prev = y, y
    shift = np.mean([placed[k] - values[k] for k in placed]) / 2
    return {k: v - shift for k, v in placed.items()}


def rank_within_season(teams: pd.DataFrame, col: str, ascending=False) -> pd.Series:
    return teams.groupby("season")[col].rank(ascending=ascending, method="min")


def fig_versus_league(teams: pd.DataFrame, league: pd.DataFrame, col: str,
                      title: str, ylabel: str, fname: str, caption: str) -> None:
    sas = teams[teams["team"] == TEAM].set_index("season")[col]
    fig, ax = plt.subplots(figsize=(9.2, 4.9))
    for t, block in teams.groupby("team"):
        if t == TEAM:
            continue
        ax.plot(block["season"], 100 * block[col], color=S.SILVER, lw=0.8,
                alpha=0.5, zorder=1)
    ax.plot(league["season"], 100 * league[col], color=S.INK_2, lw=2.2, zorder=3)
    ax.plot(sas.index, 100 * sas, color=S.SPURS, lw=2.6, zorder=4)
    ax.scatter(sas.index, 100 * sas, s=17, color=S.SPURS, edgecolors=S.SURFACE,
               lw=1.2, zorder=5)
    ax.annotate("San Antonio", (sas.index[-1], 100 * sas.iloc[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", color=S.SPURS,
                fontsize=9.5, fontweight="semibold")
    ax.annotate("League", (league["season"].iloc[-1], 100 * league[col].iloc[-1]),
                xytext=(8, 0), textcoords="offset points", va="center",
                color=S.INK_2, fontsize=9.5)
    ax.set_xlim(teams["season"].min() - 0.4, teams["season"].max() + 4.4)
    ax.set_xticks(range(2004, 2026, 3))
    S.strip(ax)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left")
    S.caption(fig, caption)
    fig.tight_layout()
    fig.savefig(FIG / fname)
    plt.close(fig)


def fig_trajectory(scored: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    for t, block in scored.groupby("team"):
        if t == TEAM or t in COMPARISONS:
            continue
        ax.plot(block["season"], block["years_ahead"], color=S.SILVER, lw=0.7,
                alpha=0.45, zorder=1)
    sas = scored[scored["team"] == TEAM]
    ends = {t: scored.loc[scored["team"] == t, "years_ahead"].iloc[-1]
            for t in COMPARISONS if (scored["team"] == t).any()}
    ends[TEAM] = sas["years_ahead"].iloc[-1]
    nudge = spread(ends, min_gap=1.15)
    for i, t in enumerate(COMPARISONS):
        block = scored[scored["team"] == t]
        if block.empty:
            continue
        ax.plot(block["season"], block["years_ahead"], color=S.SERIES[i], lw=1.6, zorder=3)
        ax.annotate(t, (block["season"].iloc[-1], nudge[t]),
                    xytext=(7, 0), textcoords="offset points", va="center",
                    color=S.SERIES[i], fontsize=9, fontweight="semibold")
    ax.plot(sas["season"], sas["years_ahead"], color=S.SPURS, lw=2.8, zorder=5)
    ax.scatter(sas["season"], sas["years_ahead"], s=20, color=S.SPURS,
               edgecolors=S.SURFACE, lw=1.3, zorder=6)
    ax.annotate("San Antonio", (sas["season"].iloc[-1], nudge[TEAM]),
                xytext=(7, 0), textcoords="offset points", va="center",
                color=S.SPURS, fontsize=9.5, fontweight="semibold")
    ax.axhline(0, color=S.INK_3, lw=1.0, zorder=2)
    ax.axvspan(DYNASTY[0] - 0.5, DYNASTY[1] + 0.5, color=S.SERIES[1], alpha=0.07, zorder=0)
    ax.annotate(f"{DYNASTY[0] - 1}-{str(DYNASTY[1])[2:]}", ((DYNASTY[0] + DYNASTY[1]) / 2,
                ax.get_ylim()[1]), xytext=(0, -14), textcoords="offset points",
                ha="center", fontsize=8.6, color=S.INK_3)
    ax.set_xlim(scored["season"].min() - 0.4, scored["season"].max() + 4.6)
    ax.set_xticks(range(2004, 2026, 3))
    S.strip(ax)
    ax.set_ylabel("Years ahead of the league's own shot chart")
    ax.set_title("Every team's shot chart, dated against the league's", loc="left")
    S.caption(fig, "Each team-season is projected onto the league's own direction of travel "
                   "through the five-zone mix, and the projection is read back as a season; the "
                   "value is that season minus the one actually played. Grey lines are the "
                   "other franchises.")
    fig.tight_layout()
    fig.savefig(FIG / "03_years_ahead.png")
    plt.close(fig)


def fig_ranking(ranking: pd.DataFrame) -> None:
    d = ranking.sort_values("years_ahead")
    y = np.arange(len(d))
    colours = [S.SPURS if t == TEAM else S.SILVER for t in d["team"]]
    fig, ax = plt.subplots(figsize=(8.8, 0.3 * len(d) + 2.6))
    ax.barh(y, d["years_ahead"], color=colours, height=0.64, zorder=2)
    for i, r in enumerate(d.itertuples()):
        v = r.years_ahead
        ax.text(v + (0.06 if v >= 0 else -0.06), i, f"{v:+.2f}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8.6, color=S.INK_2)
    ax.axvline(0, color=S.INK_3, lw=0.9, zorder=3)
    ax.set_yticks(y, d["team"])
    ax.set_ylim(-0.8, len(d) - 0.2)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=8.8)
    ax.set_xlabel("Average years ahead of the league, 2003-04 to 2024-25")
    ax.set_title("Who was actually early", loc="left")
    S.caption(fig, "Mean over every season a franchise appears. Teams that relocated or "
                   "rebranded are kept under the abbreviation the source data uses.")
    fig.tight_layout()
    fig.savefig(FIG / "04_ranking.png")
    plt.close(fig)


def fig_dynasty_mix(teams: pd.DataFrame, league: pd.DataFrame) -> None:
    lo, hi = DYNASTY
    sas = teams[(teams["team"] == TEAM) & teams["season"].between(lo, hi)]
    lg = league[league["season"].between(lo, hi)]
    cols = A.SHARE
    s = sas[cols].mean() * 100
    l = lg[cols].mean() * 100
    y = np.arange(len(cols))

    fig, ax = plt.subplots(figsize=(9.2, 4.4))
    for i, c in enumerate(cols):
        ax.plot([l[c], s[c]], [i, i], color=S.GRID, lw=2.6, zorder=1)
    ax.scatter(l.to_numpy(), y, s=80, color=S.SILVER, edgecolors=S.SURFACE, lw=2, zorder=3)
    ax.scatter(s.to_numpy(), y, s=80, color=S.SPURS, edgecolors=S.SURFACE, lw=2, zorder=3)
    for i, c in enumerate(cols):
        far = max(s[c], l[c])
        ax.text(far + 0.6, i, f"{s[c] - l[c]:+.1f}", va="center", fontsize=9,
                color=S.INK_2, fontweight="semibold")
    ax.set_yticks(y, [c.replace("share_", "") for c in cols])
    ax.set_ylim(-0.6, len(cols) - 0.4)
    ax.grid(axis="y", visible=False)
    S.strip(ax, keep=("bottom",))
    ax.tick_params(axis="y", labelsize=9.2)
    ax.set_xlabel("Share of attempts (%)")
    ax.set_title(f"The championship-era shot chart, {lo - 1}-{str(hi)[2:]}",
                 loc="left", pad=30)
    ax.text(0.0, 1.035, "Grey: the league.   Black: San Antonio.   Labels are the gap.",
            transform=ax.transAxes, fontsize=9, color=S.INK_2)
    S.caption(fig, "The corner three is where the separation is, and it is the only zone where "
                   "the gap is large. The rest of the chart is close to ordinary.")
    fig.tight_layout()
    fig.savefig(FIG / "05_dynasty_mix.png")
    plt.close(fig)


def main() -> None:
    teams = pd.read_csv(PROC / "team_seasons.csv")
    league = pd.read_csv(OUT / "league_path.csv")

    path = A.smooth_path(league)
    axis = A.LeagueAxis(path)
    scored = A.score_teams(teams, axis, EXTRAPOLATE_YEARS)
    print("league direction of travel, loadings on the five zones")
    print(axis.loadings.round(3).to_string())
    print(f"share of the league path's variation on this one axis: "
          f"{100 * axis.explained:.1f}%\n")
    scored["corner_rank"] = rank_within_season(scored, CORNER)
    scored["three_rank"] = rank_within_season(scored, "three_rate")
    scored["mid_rank"] = rank_within_season(scored, MID, ascending=True)
    scored["value_rank"] = rank_within_season(scored, "profile_value")
    scored.round(5).to_csv(OUT / "years_ahead.csv", index=False)

    ranking = (scored.groupby("team")
               .agg(seasons=("season", "size"), years_ahead=("years_ahead", "mean"),
                    off_axis=("off_axis", "mean"),
                    corner_rank=("corner_rank", "mean"),
                    three_rank=("three_rank", "mean"))
               .reset_index())
    ranking.round(4).to_csv(OUT / "team_ranking.csv", index=False)

    # The construction this metric replaced, kept so the comparison in the
    # write-up is checkable rather than asserted.
    nn = A.nearest_neighbour(scored, path, axis)
    nn.round(4).to_csv(OUT / "nn_comparison.csv", index=False)
    pinned = int(nn["outside_path"].sum())
    print(f"nearest-neighbour check: {pinned} of {len(nn)} team-seasons "
          f"({100 * pinned / len(nn):.0f}%) sit outside the league path's own "
          f"range and would be pinned to one of its ends")
    print(nn.loc[nn["team"].isin(["HOU", "DEN", "MEM"])]
          .sort_values("nn_minus_projection")
          .head(3)[["team", "season", "nn_years", "years_ahead"]]
          .to_string(index=False), "\n")

    sas = scored[scored["team"] == TEAM].copy()
    sas.round(5).to_csv(OUT / "spurs_path.csv", index=False)

    fig_versus_league(
        teams, league, "three_rate",
        "San Antonio never led the league in three-point volume",
        "Share of attempts from three (%)", "01_three_rate.png",
        "Every franchise in grey, the league in dark grey, San Antonio in black. Twenty-two "
        "seasons of a team whose reputation is built on being early to the three, sitting in "
        "the middle of the pack for almost all of them.")
    fig_versus_league(
        teams, league, CORNER,
        "The corner is a different story",
        "Share of attempts from the corner three (%)", "02_corner_rate.png",
        "Corner threes as a share of all field goal attempts. This is the shot the reputation "
        "is actually about.")
    fig_trajectory(scored)
    fig_ranking(ranking)
    fig_dynasty_mix(teams, league)

    print(f"{len(scored):,} team-seasons scored; "
          f"{int(scored['clipped'].sum())} hit the end of the extended axis")
    print(f"\n--- San Antonio, season by season ---")
    print(sas[["season", "three_rate", "three_rank", CORNER, "corner_rank",
               MID, "mid_rank", "profile_value", "value_rank", "years_ahead",
               "off_axis"]]
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    lo, hi = DYNASTY
    era = sas[sas["season"].between(lo, hi)]
    print(f"\n--- {lo - 1}-{str(hi)[2:]} ---")
    print(f"three-point volume rank, mean {era['three_rank'].mean():.1f} of 30")
    print(f"corner-three rank,      mean {era['corner_rank'].mean():.1f} of 30")
    print(f"mid-range avoidance,    mean {era['mid_rank'].mean():.1f} of 30")
    print(f"shot profile value,     mean {era['value_rank'].mean():.1f} of 30")
    print(f"years ahead,            mean {era['years_ahead'].mean():+.2f}")

    print("\n--- most and least advanced franchises, whole sample ---")
    print(pd.concat([ranking.nlargest(6, "years_ahead"),
                     ranking.nsmallest(4, "years_ahead")])
          .to_string(index=False, float_format=lambda v: f"{v:.2f}"))
    print("\n--- least like anyone else, whichever direction ---")
    print(ranking.nlargest(5, "off_axis")
          .to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\nSan Antonio overall: "
          f"{ranking.loc[ranking['team'] == TEAM, 'years_ahead'].iloc[0]:+.2f} years, "
          f"rank {int(ranking['years_ahead'].rank(ascending=False)[ranking['team'] == TEAM].iloc[0])}"
          f" of {len(ranking)}")


if __name__ == "__main__":
    main()
