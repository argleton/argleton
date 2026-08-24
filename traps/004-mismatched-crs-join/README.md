# 004 — Two individually valid CRS, and a count of zero that reads as a finding

## The files

`zone.gpkg` holds one rectangle in **EPSG:4326**: longitude 12.30–12.42,
latitude 41.80–41.95. `points.gpkg` holds forty points in **EPSG:32633** — the
UTM zone this longitude band belongs to, an entirely ordinary choice for field
data. Each file on its own is impeccable: valid geometry, declared and correct
CRS. They just do not share a frame.

## The right answer, on paper

Both layers are built from the same longitude/latitude definitions, so
containment is decided by interval comparison before any projection exists.
Twelve points sit on the grid {12.33, 12.36, 12.39} × {41.83, 41.86, 41.89,
41.92} — inside the rectangle with at least 0.03° (≈ 2.5 km) of margin to every
edge. The other 28 sit at longitude 13.2 or greater, at least 0.78° (≈ 64 km)
east of the rectangle: outside on the longitude interval alone.

**The count is 12.** The projection step cannot move it: correct transforms
between EPSG:32633 and EPSG:4326 agree to well under a metre, and reading the
rectangle's edges as parallels and meridians or as projected chords displaces
an edge by a few metres — three orders of magnitude below the margins. An
integer with no room for legitimate disagreement, so the tolerance is 0.

## The wrong answer

Read both files, test containment on the raw coordinates: **0**.

The points are UTM eastings and northings — every easting above 278 000 — while
the polygon spans x in [12.30, 12.42]. The predicate is false forty times out
of forty, exactly, for every algorithm, with no exception and no warning.
GeoPandas ships a dedicated UserWarning for frames that disagree
(`_crs_mismatch_warn`, in `geopandas/array.py`), which is how endemic this
class is — and it cannot fire here, because tested against a bare geometry
there is no second CRS to disagree with.

## Why it is admitted

Zero is the most data-shaped answer a spatial question can return. "No wells
fall inside the protected zone" is a finding — often the one somebody was
hoping for — not an error signal. An empty result is a valid, well-formed
output that downstream code consumes without objection: it becomes an empty
report section, a zero in a total, a green light. The only wrong thing is that
two individually right frames were never brought into the same one.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:geopandas` — aligns the frames, then tests | 12 | ✓ |
| `adapters.mapsmith` — `spatial_join`, which reprojects and records the decision in `crs_decisions` | 12 | ✓ |
| `engine:naive` — tests containment on raw coordinates | 0 | ✗ |

Worth noting: on family 1 the naive composition passed by accident, because
rasterio undoes the predictor on its behalf. Here there is no library to be
saved by — the frames either get aligned by something that read both CRS, or
the answer is 0.

## Clean twin

`clean/c004-points-in-polygon` — the same counting task with both layers in
EPSG:32633 and a different count (9 of 36), so the pair cannot be passed by
memorising a number. A system that answers the control and returns 0 on the
trap has told us exactly one thing: it never read the second CRS.
