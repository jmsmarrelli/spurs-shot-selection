# Method notes

The metric, the version of it that was wrong, and what the whole thing cannot see.

## The unit

A team-season's mix across five zones: restricted area, paint outside it,
mid-range, corner three, above the break. Five numbers summing to one.

Coarse on purpose. The NBA's action-type vocabulary was rewritten between 2007
and 2009 — "pull-up jump shot" and "step back jump shot" do not exist in the
2003-04 file — and its shot coordinates were recorded differently before 2010-11,
when roughly a quarter of all attempts carry the rim's own coordinate rather than
the shooter's. A five-bucket zone label is the only description of a shot that
means the same thing at both ends of this sample, so it is what the analysis runs
on, and nothing here depends on a coordinate comparison across 2010-11.

## Dating a shot chart

The league's own mix traces a path through the five-zone simplex, one point per
season. Every team-season is somewhere near it. "Years ahead" is the distance
along that path, converted to seasons.

**The construction that failed.** Find the nearest point on the path and read off
its year. It fails in two unrelated ways, and neither is the one I expected.

*It saturates.* The nearest point can only be a season the league actually
played, so any team past either end of the path is pinned to that end. The
2017-18 Rockets project past the 2024-25 league average; a nearest-neighbour
match gives them +3 years, because there is nothing further along to match them
to. Denver in 2005-06 sits behind the 2003-04 league average and comes out
*contemporary*, for the same reason in reverse. 139 of the 659 team-seasons here
— 21% — are outside the path's range, and every one of them would be truncated.

*It mixes two ideas.* A team can be far along the path or far away from it, and
a distance match assigns both to whichever season is nearest. Being unusual and
being early become the same number.

`output/nn_comparison.csv` reports both metrics for every team-season, so the
comparison is checkable rather than asserted.

**The construction that works.** Take the first principal component of the
league path. It carries 98.7% of the path's variation, and loads:

| Zone | Loading |
|---|---|
| Mid-range | −0.795 |
| Above-the-break three | +0.554 |
| Paint, off the rim | +0.185 |
| Corner three | +0.140 |
| At the rim | −0.085 |

Project each team-season onto that axis; the league's own score is monotone in
season, so the projection inverts to a year, and it extrapolates rather than
saturating. Movement *across* the axis — a team that is unusual rather than early
— becomes its own quantity rather than contaminating the first.

**What neither construction fixes.** Look at those loadings. The mid-range term
is half again the size of the above-the-break term, because the mid-range is
where the league moved most, which means *not taking mid-range shots* scores as
modern regardless of what replaced them. Memphis in 2003-04 took 28.4% of its
shots from the mid-range against a league average of 35.8% — the lowest share in
the league — and 19.3% from three against a league average of 18.3%, which is
ordinary. They emptied the mid-range into the restricted area. Nearest-neighbour
calls them +8.0 years ahead; the projection calls them +7.8. This is not an
artifact to be engineered away: it is what "resembles the league's future"
means when the league's future was defined mostly by a subtraction. The
`off_axis` column is what flags it, and any use of the headline number should be
read next to it.

Two details:

* The path is smoothed with a three-season centered window before the
  decomposition. Season-to-season wobble in a thirty-team average is small but
  not zero, and matching against an unsmoothed path turns it into fake precision.
* Teams past either end of the observed path are extrapolated along the axis and
  then clipped at eight years. 46 of 659 team-seasons hit that clip, all of them
  extreme in the expected directions, and `output/years_ahead.csv` flags each one.

## What "years ahead" is not

It is not a quality measure. A shot chart five years ahead of the league is a
shot chart that resembles the future, and the future is not automatically better
for the team that has it: the 2004-05 Suns were years early and would have been
early in a way that did not survive the officiating of the time.

It is also not an intent measure. A team can end up modern by design, by roster
accident, or by having no center. Nothing here distinguishes them.

## Franchise continuity

Teams are kept under the abbreviation the source file uses, which means Seattle
appears for five seasons and Oklahoma City separately for seventeen, and Brooklyn
and New Jersey are separate rows. Ranking franchises by a mean over the seasons
they appear therefore puts short samples near the top, and Seattle at +3.71 over
five seasons is doing less work than Houston at +5.75 over twenty-two. The season
counts are in the ranking table for exactly that reason.

## Where this is weakest

**Five zones cannot see distance drift.** Above-the-break threes moved outward
across this sample — the league's average three is longer than it was — and this
metric is blind to it. A team that pioneered the 28-footer would score as
ordinary.

**The corner-three finding is a share, not a strategy.** San Antonio took a
larger share of its shots from the corner than almost anyone for a decade. That
is consistent with a deliberate design and equally consistent with having Bruce
Bowen, and this data cannot separate a system from a personnel accident.

**Nothing here is about efficiency.** The "value of the shot mix" number holds
conversion at the league's own rate in each zone, deliberately, so that it moves
only when selection moves. A team that took worse shots and made more of them
looks worse here and scored more points, which is the correct behavior for a
selection metric and the wrong number to quote at anyone about offense.

**Free throws are absent.** Twenty-two seasons of a league that has repeatedly
changed how it officiates contact, measured with an instrument that cannot see a
foul.
