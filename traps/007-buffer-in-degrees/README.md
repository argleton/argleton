# 007 — A distance of 500, applied in the layer's units instead of the question's

## The file

`wells.gpkg` holds 25 wells in **EPSG:4326**. W-1 sits at (12.40, 41.90); three
wells lie within 400 metres of it, the other 21 lie kilometres away. Everything
about the file is honest — valid points, declared CRS — and so is the number
500 in the question. What is implicit is the unit it gets applied in.

## The right answer, on paper

In the local metric at 41.9°N (1° of latitude = 111.1 km, 1° of longitude =
82.9 km), the three near wells sit at ~300 m, ~398 m and ~359 m from W-1; the
nearest excluded well is at 6,932 m. **The count is 3.** The margins carry the
derivation: at these distances a flat-earth approximation, a geodesic and a
UTM-planar distance agree to within centimetres, while the included/excluded
gap is three orders of magnitude wider than any method disagreement.
Tolerance 0.

## The wrong answer

Buffer W-1 by 500, count the wells inside: **24 — every single one**.

Shapely, GeoPandas and PostGIS all buffer in the layer's own units by design,
and none of them can know the caller meant metres. A buffer of 500 *degrees*
spans longitudes −487.6 to 512.4: the whole coordinate space of the file, and
then the planet, repeatedly. No exception, no warning — the buffer is a
perfectly valid polygon, just an absurd one that nothing downstream ever looks
at. Only the count survives, and the count looks fine.

## Why it is admitted

This family's classic demonstration — "the buffered *area* is planet-sized" —
is loud, and a loud failure belongs in an ordinary test suite. The trap plants
the quiet variant: a **count**. "24 wells within half a kilometre" is an
ordinary number for a dense urban wellfield, and a count carries no trace of
the geometry that produced it. The figure 500 is exactly what the question
said; the only implicit thing was the unit.

## Observed

| adapter | answer | |
|---|---|---|
| `engine:geopandas` — projects to the local UTM zone, then measures | 3 | ✓ |
| `adapters.mapsmith` — `buffer_layer`, whose contract is metres (auto-UTM on geographic layers, decision recorded), then a within-join | 3 | ✓ |
| `engine:naive` — buffers 500 in the layer's units | 24 | ✗ |

The MapSmith pass is earned the same way family 4's was: not by a library that
happens to save the caller, but by a tool contract that names the unit
(*metres, always*) and records the reprojection decision in the manifest.

## Clean twin

`clean/c007-distance-in-metres` — the same question on a layer already in
EPSG:32633: five wells within 460 m (offsets exact by Pythagoras), the rest at
2.5 km or more. The trap and its control differ in exactly one thing: whether
the layer's unit is the one the question uses.
