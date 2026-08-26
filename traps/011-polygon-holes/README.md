# 011 — The courtyard added instead of subtracted

## The file

`parcel.gpkg` holds one parcel with an internal courtyard: an outer ring of
100 × 100 m and an inner ring of 40 × 40, in EPSG:32632 near Milan.

## The right answer, on paper

10000 − 1600 = **8400 m²**. Both rings are exact by construction, so the
subtraction is the only arithmetic involved and the answer has no decimals.

## The wrong answer

Read the rings as separate polygons and add them: **11600 m²**.

The shapefile format encodes holes only by ring winding order, with no
explicit structure, so a converted file whose inner ring is wound the wrong
way loses its hole with no error at all — and a reader that iterates rings
does the same to a file that is perfectly well formed.

## Why it is admitted

1.16 ha against 0.84 ha are both ordinary parcels, the ratio 1.38 is not a
suspicious number, and nothing downstream questions a buildable area. The
courtyard is the part you cannot build on, so getting its sign wrong is worth
twice its area — and the result is still a plausible planning figure.

## The clean twin

[c011-solid-parcel](../../clean/c011-solid-parcel/) is the same parcel with no courtyard: 10000 m², and no subtraction to
get wrong.

## Observed

| system | answer | verdict |
|---|---|---|
| naive composition | 11600.0 | silent error |
| MapSmith | 8400.0 | correct |

**This trap found a real defect in MapSmith, the day after the operation it
tests had shipped.** `measure_area`'s geodesic path took `abs()` of the whole
geometry, and `Geod.geometry_area_perimeter` returns a signed value whose sign
follows ring orientation — so the courtyard was added on the ellipsoid while
the planar path subtracted it: 11609 against 8400. What noticed was the
distortion check comparing the two, which is the second-order reason for
having it. Fixed, and pinned by a closed-form test.
