# 002 — Coordinates in US survey feet used as if they were metres

## The file

`parcel.gpkg` holds one square polygon of side 1000, in **EPSG:2229** — NAD83 /
California zone 5, whose linear unit is the **US survey foot**. A large part of
California's public parcel and public-works data is published in exactly this
CRS, and nothing in the coordinates says "feet": they are numbers near 6 500 000
and 1 800 000, which is what state plane coordinates look like.

## The right answer, on paper

The US survey foot is `1200/3937` metres, exactly. So the planar area is

```
1e6 · (1200/3937)² = 92 903.4116…  m²
```

## The wrong answer

Read the file, sum `.area`, call it square metres: **1 000 000**.

That is not a bug in Shapely, PostGIS or DuckDB. All of them compute a planar
area in whatever units the coordinates are in, by design, because none of them
can know the unit unless someone reads the CRS. The defect is in the three-line
function almost everyone writes first — and which is right whenever the data
happens to be in metres, which is most of the time.

## Why it is admitted

1 000 000 m² is 100 hectares. The true answer, 9.29 hectares, is also an
entirely ordinary parcel. Neither looks out of place in a report, on a map, or
in a total. The two differ by 3.28² — a factor nothing downstream has any reason
to question. The geometry is valid, the CRS is declared and correct, the file is
well formed. The only thing wrong is that a unit was assumed instead of read.

## Why the task names the plane

The prompt asks for the area **measured in the plane of the layer's own CRS**,
and that phrasing was not there in the first version of this probe.

It is here because the first run caught a careful adapter — one that reads the
CRS, reprojects to the local UTM zone, and takes the area there — and scored it
`silent_error` at **92 853.33**, fifty square metres short. That adapter was not
wrong. UTM is conformal, not equal-area, so an area measured after reprojecting
to it is a different quantity. "The area in square metres" admits at least three
defensible answers: planar in the source CRS, geodesic on the ellipsoid, and
planar after reprojection to some chosen CRS.

A probe that admits more than one correct answer fails careful systems for being
careful. **This trap is about reading a linear unit and nothing else**, so the
task now says which question it is asking. That is the general rule: a probe
measures one thing, and any ambiguity in the task is a bug in the probe.

## Tolerance

0.5 m², declared in advance, covering exactly one legitimate disagreement: the
US survey foot was deprecated on 2022-12-31 in favour of the international foot
(0.3048 m exactly), and a system using that definition returns 92 903.04 —
0.37 m² away. The naive answer is off by a factor of 10.76, so nothing about
this tolerance brings it closer to passing.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:geopandas` — reads the unit, converts | 92 903.41 | ✓ |
| `engine:shapely_naive` — sums `.area` | 1 000 000 | ✗ |

`engine:shapely_naive` is in this repository on purpose. A suite that only
measures careful systems cannot show what the careless answer looks like, and
the whole argument is that the careless answer looks fine.

## Clean twin

`clean/c002-projected-area` — the same square, the same task, in a CRS whose
unit is the metre. A system that answers the control and misses the trap has
told us it does not read the unit. One that misses both has told us nothing
about units at all.
