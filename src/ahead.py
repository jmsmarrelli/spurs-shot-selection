"""How far along the league's own path a team's shot chart sits.

The league's shot mix moved in one direction for twenty-two years: out of the
mid-range, into the corners and above the break. That makes the league average a
*path* through the five-zone simplex, indexed by season, and it makes a natural
question available - not "did this team shoot more threes", which any two teams
can argue about, but **which season's league average does this team's shot chart
look like?** A team whose 2013-14 mix matches the league's 2018-19 average was,
in the only sense the phrase can be made precise, five years ahead.

## Why this is not a nearest-neighbour match

The obvious implementation is to find the point on the path closest to the team
and read off its year. I built that first and it fails in two unrelated ways.

It saturates: the nearest point can only be a season the league actually played,
so a team past either end of the path gets pinned to that end. Twenty-one per
cent of team-seasons in this sample sit outside the path's own range, and every
one of them would have its score truncated.

And it puts two different ideas in one number: a team can be far *along* the path
or far *away from* it, and a nearest-neighbour match assigns both to whichever
season happens to be closest.

So: take the first principal component of the league path, project every
team-season onto it, and convert the projection back to a year using the league's
own monotone score-to-season curve. What is left over, the distance off the axis,
becomes an "unlike anyone" measure reported separately.

What this does *not* fix is the axis's own shape. It loads -0.795 on the
mid-range and +0.554 above the break, because that is where the league moved, so
a team that emptied its mid-range into the rim without adding a single three
still scores as modern. Memphis in 2003-04 is the case: mid-range 28.4% against a
league 35.8%, three-point rate 19.3% against a league 18.3%. Both constructions
call them roughly eight years early. That is what the measurement means rather
than something it gets wrong, and `docs/method.md` says so.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ZONES = ["Restricted Area", "In The Paint (Non-RA)", "Mid-Range",
         "Corner 3", "Above the Break 3"]
SHARE = [f"share_{z}" for z in ZONES]


def smooth_path(league: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    """Season-to-season wobble in a league average is noise, not direction."""
    out = league.sort_values("season").copy()
    out[SHARE] = out[SHARE].rolling(window, center=True, min_periods=1).mean()
    return out


class LeagueAxis:
    """The league's direction of travel, and the year each point on it maps to."""

    def __init__(self, path: pd.DataFrame):
        self.years = path["season"].to_numpy(dtype=float)
        mat = path[SHARE].to_numpy()
        self.centre = mat.mean(axis=0)
        centred = mat - self.centre
        _, _, vt = np.linalg.svd(centred, full_matrices=False)
        axis = vt[0]
        # Orient the axis so that later seasons score higher, whatever sign the
        # decomposition happened to return.
        if np.dot(centred[-1] - centred[0], axis) < 0:
            axis = -axis
        self.axis = axis
        self.scores = centred @ axis
        if not np.all(np.diff(self.scores) > -1e-9):
            raise ValueError("the league's score is not monotone in season; "
                             "the projection cannot be inverted to a year")
        self.loadings = pd.Series(axis, index=SHARE)
        self.explained = float((self.scores.var() * len(self.scores))
                               / (centred ** 2).sum())

    def project(self, mat: np.ndarray) -> np.ndarray:
        return (mat - self.centre) @ self.axis

    def to_year(self, score: np.ndarray, extrapolate: float) -> np.ndarray:
        """Invert the monotone score-to-season curve, with a bounded extension."""
        year = np.interp(score, self.scores, self.years)
        head = (self.scores[1] - self.scores[0]) / (self.years[1] - self.years[0])
        tail = (self.scores[-1] - self.scores[-2]) / (self.years[-1] - self.years[-2])
        below, above = score < self.scores[0], score > self.scores[-1]
        year = np.where(below, self.years[0] + (score - self.scores[0]) / head, year)
        year = np.where(above, self.years[-1] + (score - self.scores[-1]) / tail, year)
        return np.clip(year, self.years[0] - extrapolate, self.years[-1] + extrapolate)

    def off_axis(self, mat: np.ndarray) -> np.ndarray:
        """How far a team sits from the axis, in share units. Unlike, not early."""
        centred = mat - self.centre
        along = np.outer(centred @ self.axis, self.axis)
        return np.linalg.norm(centred - along, axis=1)


def score_teams(teams: pd.DataFrame, axis: LeagueAxis, extrapolate: float) -> pd.DataFrame:
    mat = teams[SHARE].to_numpy()
    out = teams.copy()
    out["axis_score"] = axis.project(mat)
    out["matched_season"] = axis.to_year(out["axis_score"].to_numpy(), extrapolate)
    out["years_ahead"] = out["matched_season"] - teams["season"].to_numpy()
    out["off_axis"] = axis.off_axis(mat)
    lo = axis.years[0] - extrapolate + 1e-9
    hi = axis.years[-1] + extrapolate - 1e-9
    out["clipped"] = (out["matched_season"] <= lo) | (out["matched_season"] >= hi)
    return out


def nearest_neighbour(scored: pd.DataFrame, path: pd.DataFrame,
                      axis: LeagueAxis) -> pd.DataFrame:
    """The metric this project does not use, for comparison.

    Match each team-season to the closest point on the league path and read off
    its year. Reported alongside the projection so the difference between the two
    is a number in a file rather than a claim in a README.
    """
    mat = scored[SHARE].to_numpy()
    P = path[SHARE].to_numpy()
    years = path["season"].to_numpy(dtype=float)
    d2 = ((mat[:, None, :] - P[None, :, :]) ** 2).sum(axis=-1)
    nn_year = years[d2.argmin(axis=1)]
    score = axis.project(mat)
    out = scored[["team", "season"]].copy()
    out["nn_years"] = nn_year - scored["season"].to_numpy()
    out["years_ahead"] = scored["years_ahead"].to_numpy()
    out["nn_minus_projection"] = out["nn_years"] - out["years_ahead"]
    out["outside_path"] = (score < axis.scores.min()) | (score > axis.scores.max())
    return out
