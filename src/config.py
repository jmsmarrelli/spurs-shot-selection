"""Paths, constants and the handful of knobs the pipeline exposes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
FIG = ROOT / "figures"
OUT = ROOT / "output"

for d in (RAW, PROC, FIG, OUT):
    d.mkdir(parents=True, exist_ok=True)

FIRST_SEASON = 2004
LAST_SEASON = 2025
SEASONS = list(range(FIRST_SEASON, LAST_SEASON + 1))

TEAM = "SAS"
TEAM_NAME = "San Antonio Spurs"
# The six title-adjacent seasons the argument is usually made about.
DYNASTY = (2011, 2016)
COMPARISONS = ["HOU", "GSW", "PHX", "MIA", "BOS"]

RIM_Y = 5.25
HEAVE_DIST = 30.0
HEAVE_SECS = 2.0

# The league's own trajectory is only observed for the seasons in the file. To
# score a team that is further along it than the league ever got, the trajectory
# is extended at both ends using the slope of its last few seasons - no further
# than this, and every team-season that lands on the extension is counted and
# reported rather than quietly clipped.
EXTRAPOLATE_YEARS = 8
TREND_WINDOW = 5

MIN_FGA = 2000    # a team-season below this is a lockout or a data gap
SEED = 20240117
