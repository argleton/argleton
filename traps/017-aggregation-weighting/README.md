# 017 — Rates averaged as though the places were the same size

## The file

`municipalities.gpkg` holds three: two with 1000 in the labour force at 20%
unemployment, and one with 98000 at 1%.

## The right answer, on paper

A rate is a ratio of totals. Unemployed: 200 + 200 + 980 = 1380. Labour force:
100000. The area's rate is 1380/100000 = **1.38%** exactly.

## The wrong answer

Average the rate column: (20 + 20 + 1)/3 = **13.67%**. It is the obvious
aggregation, every tool offers it as `mean`, and it is right whenever the
units being averaged are the same size.

## Why it is admitted

Both numbers are ordinary unemployment rates and neither is out of range;
13.67% describes a region in difficulty and 1.38% one at full employment, and
the report that carries either looks identical. The error grows with the size
imbalance between the units, which is exactly what administrative geography is
made of: a metropolis and the villages around it.

## The clean twin

[c017-equal-populations](../../clean/c017-equal-populations/) has three municipalities of the same size, where weighted and unweighted
agree at 15% — which is what makes the habit survive.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 13.6667 | silent error |
| MapSmith | 1.38 | correct |

This is the one family in this tier that is not geometric at all, and that is
the point: an agent aggregates attributes more often than it reprojects.
`aggregate_weighted` returns the unweighted mean beside its answer, so the
difference is visible rather than hidden.
