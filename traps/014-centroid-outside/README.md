# 014 — The parcel located by a point that is not on it

## The file

`parcel.gpkg` holds an L-shaped parcel: a 100 × 20 bar plus a 20 × 80 upright,
3600 m². `districts.gpkg` holds district A — exactly that L — and district B,
the notch the L does not occupy.

## The right answer, on paper

Every point of the parcel is in **A**. That is what containment means, and
it is what the question asks.

## The wrong answer

Reduce the parcel to its centroid and ask which district contains it: **B**.

The composite centroid is at x = (2000·50 + 1600·10)/3600 = 32.22 and
y = (2000·10 + 1600·60)/3600 = 32.22 — a point in the notch, on no part of
the parcel at all.

## Why it is admitted

A district name is the least suspicious answer form there is: no magnitude to
sanity-check, no units, no precision. L-shaped, U-shaped and crescent parcels
are ordinary — a plot around a courtyard, a municipality wrapping a bay — and
the centroid of any of them can sit outside.

## The clean twin

[c014-convex-parcel](../../clean/c014-convex-parcel/) asks the same question of a rectangular parcel, whose centroid is on it:
centroid and containment agree, and locating by centroid works.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | B | silent error |
| MapSmith | A | correct |

`point_on_surface` exists because of this trap: a representative point verified
to lie ON its own feature, which is a postcondition rather than an opinion.
