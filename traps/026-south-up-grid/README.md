# 026 — raster affine

**A DEM whose rows run south to north, which is legal, and the cell size that
disappears with it.**

`site.tif` is a 400 m construction site: a plane rising 1 m per 10 m cell
towards the east, so the ground slopes at **5.7106°** everywhere. The question is
how steep it is.

rasterio and a plain numpy gradient answer **5.71**. whitebox-workflows answers
**43.99**. MapSmith answered 43.99 too, until this probe was built.

## Why the file is not wrong

A GeoTIFF's geotransform has six numbers and the fifth is the north-south pixel
size. It is negative for a north-up image — row 0 at the top, rows counting
southwards. A **positive** fifth number is equally valid and says the rows run
the other way, with the origin at the south-west corner.

That form is ordinary. NetCDF, GRIB and HDF products index latitude in
increasing order, because that is how a coordinate axis is written, so a direct
conversion to GeoTIFF produces a south-up grid. So do several Surfer and GMT
exports. GDAL reads all of them and reports the transform faithfully — including
that on this file `bounds.top` (4500000) is *south* of `bounds.bottom`
(4500400).

## The defect

```python
read_raster("site.tif").metadata()
#   north-up twin:  west=500000.0   resolution_x=10.0
#   this file:      west=0.0        resolution_x=1.0
```

An engine that builds its own grid model and cannot express a positive fifth
number has to do something, and what it does here is discard the georeferencing:
forty by forty cells of one metre, at the origin.

The elevations are untouched. The shape is untouched. **The coordinate system is
untouched** — it still reports EPSG:32633. Only the size of a cell is gone.

A slope is a rise over a run, so a run ten times too short gives

```
atan(1 / 1) = 45.0°     instead of     atan(1 / 10) = 5.7106°
```

## Why 45° is plausible

45° is a slope. Steep — a one-in-one bank, a scree slope, a quarry face — and
entirely ordinary for a DEM to contain some. The answer arrives as a single
number with nothing beside it to compare against.

What makes it dangerous is the **direction**. Slope thresholds are one-sided:
buildable under 15°, machinery under 20°, landslide susceptibility above 30°. A
site that is genuinely 5.7° and reports 45° does not produce a wrong map, it
produces a *refusal* — the ground is rejected as unbuildable, the excavation is
priced for rock, the hazard layer lights up. Each of those is expensive, and
none of them prompts anybody to recheck a DEM, because the answer agreed with
the fear.

And it is **uniform**. Every cell is wrong by the same factor, so the slope map
has the right shape, the right pattern, the right relative highs and lows. It is
the correct picture of the site with the wrong number on the legend.

Note also that the ratio is not ten. Slope is an arctangent, not a proportion,
so the error is a factor of about eight — and an error of "ten times" is the one
somebody would look for.

## What it did to MapSmith

MapSmith failed this probe when it was written, and the way it failed is worth
recording:

| | |
|---|---|
| mean slope | **43.99** where the truth is 5.71 |
| output geotransform | `c=0.0, a=1.0` — the origin, at a tenth of the site's size |
| output CRS | EPSG:32633, correct |
| verification checks | **five of five passed** |

`crs_present`, `crs_matches`, `shape_preserved`, `result_not_empty`,
`values_in_expected_range` — all green, beside a slope raster 4 500 km from the
site. `crs_matches` passes precisely because the error is not in the CRS: the
coordinate system survived and the geotransform did not, and no check compared
the output's transform with the input's.

That is the same shape as this project's first published result, where MapSmith
scored 0.00 with seven green checks and none of them looked at whether the
number was right.

## The clean twin

[`c026-north-up-grid`](../../clean/c026-north-up-grid/) is the same plane, the
same cells, the same elevations, stored north-up. Every engine answers it
correctly.

The pair separates "mishandles the axis direction" from "cannot compute a slope",
and it catches the over-correction: a system that has learned about south-up
grids and now flips every raster it reads answers the twin upside down — which
on a plane tilted east is invisible in the slope, and not in the aspect.
