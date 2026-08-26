# 015 — The wells on the seam that belong to neither district

## The file

`districts.gpkg` partitions the study area into x ∈ [0, 50] and x ∈ [50, 100],
sharing the line x = 50. Four of the twelve wells in `wells.gpkg` sit exactly
on that line.

## The right answer, on paper

**12.** The districts leave no gap, so every well is in the study area — and
the answer stays 12 whichever district the seam wells are assigned to,
because the question is about the partition and not about either district.

## The wrong answer

Join with `within` and count: **8**. Strict containment excludes the boundary,
so a point exactly on a shared edge is in neither polygon and vanishes from a
partition that covers it. No error, no warning: the join returns fewer rows.

## Why it is admitted

8 of 12 is an ordinary spatial-join result — nobody expects every feature to
match — and the four that vanished appear nowhere. The case is common by
construction: administrative boundaries are shared edges, and features
digitised against them land exactly on the line.

## The clean twin

[c015-wells-off-the-seam](../../clean/c015-wells-off-the-seam/) moves the four seam wells one metre west. `within` and boundary-inclusive
predicates agree at 12.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 8 | silent error |
| MapSmith | 12 | correct |

`count_in_polygons` states its boundary rule and counts the points that fell in
no polygon at all — which is the number that makes this failure visible.
