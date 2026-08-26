# 012 — Overlapping concessions added instead of united

## The file

`overlap.gpkg` holds two licence areas of 10000 m² each. The second starts
60 m into the first, so they share a 40 × 100 m strip.

## The right answer, on paper

Inclusion–exclusion: 10000 + 10000 − 4000 = **16000 m²** of ground. The strip
is counted once because it is one piece of ground, whatever the number of
licences over it.

## The wrong answer

Sum the area column: **20000 m²**. It is the natural way to answer 'how much
in total', and it is right whenever the features do not overlap — which is
most of the time, which is why the habit survives.

## Why it is admitted

2 ha against 1.6 ha are both ordinary concession totals and nothing in the
result hints at a shared strip. The documented real-world case is mosaicked
satellite tiles, which overlap by construction: adding their footprints
inflates every coverage figure by the overlap, silently.

## The clean twin

[c012-disjoint-concessions](../../clean/c012-disjoint-concessions/) has the same two squares 60 m apart. Sum and union agree at 20000, so a
system that adds areas answers it correctly.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 20000.0 | silent error |
| MapSmith | 16000.0 | correct |

Second probe of this family: [019](../019-partial-overlap/), where the unit of
measurement quietly changes from the square metre to the parcel.
