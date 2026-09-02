# 031 — The easement counted as land, because of the direction it was written in

## The file

`plot.shp` holds one survey plot of 200 × 150 m with an easement of 40 × 25
running through it, in EPSG:32632 near Milan. Two rings, and both are wound
**clockwise**.

## The right answer, on paper

30000 − 1000 = **29000 m²**. Both rectangles are exact by construction and the
fixture is already in a metric CRS, so the subtraction is the only arithmetic
involved.

## The wrong answer

**31000 m²**, the easement added rather than subtracted — a gap of exactly twice
its own area, because the same 1000 m² moves from one side of the subtraction to
the other.

A shapefile has no nesting. Whether a ring is a shell or a hole is decided by
the direction it is wound and by nothing else, and GDAL applies that rule as
documented: `OGR_ORGANIZE_POLYGONS` defaults to `ONLY_CCW` for this driver,
under which a clockwise ring is a shell. So the reader does exactly what the
format tells it to and returns two overlapping shells instead of one polygon
with a hole.

Nothing warns. The bounding box, the coordinates, the CRS and the feature count
are all right; the outline of the plot is exactly where it should be. The only
thing that is wrong is which of the two rings is a gap, and that is not a
quantity anybody checks.

## Why it is plausible

3.1 hectares against 2.9. An error of 6.9% is smaller than the difference
between two surveys of the same field, the number is not round in a suspicious
way, and it is not off by a factor anybody would recognise.

The direction of the error is the quiet part: the easement is counted as land
rather than as a gap, so the mistake is always in the owner's favour. An error
that flatters is one nobody goes looking for.

## What a careful reader does

The geometry that comes back is invalid, and GEOS names the reason exactly —
`Nested shells`. A reader that checks validity, repairs and says what it
repaired gets 29000 and can explain the 31000. That is the whole gap between the
two rows in the results table, and it costs one call.

## Why the fixture patches the bytes

Writing this polygon through OGR does not produce this file. Measured on
2026-09-02 by reading the record back out of the `.shp`: the shapefile **writer
normalises ring direction**, so a hole handed to it clockwise lands on disk
anticlockwise. `build.py` therefore writes the correct file and reverses the
inner ring's point order in place — a local edit that changes no coordinate,
which is why the arithmetic above stays exact.

That asymmetry is the provenance of the defect rather than an inconvenience: a
file with the wrong winding does not come from GeoPandas, GDAL or QGIS writing a
shapefile. It comes from a converter, an exporter or a hand-rolled writer, which
is where it comes from in the field.

## Not the same as 011

Trap [011](../011-polygon-holes/) is a well-formed file whose consumer adds the
inner ring instead of subtracting it — the defect is in the code. Here the
defect is in the file, and a correct reader following the documented rule
produces the wrong answer. 011's README already stated this mechanism in prose;
this probe is what turns that sentence into a measurement.
