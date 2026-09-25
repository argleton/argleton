# 024 — pixel is point

**A grid whose own metadata says its values sit at the nodes, read by an engine
that does not look — and by code that corrects it twice.**

`hollow.tif` is an 8×8 digital elevation model at 30 m spacing, a shallow
depression with exactly one lowest cell. The question is where that cell is.

The right answer is an easting of **412105**. Whitebox says **412120**, half a
cell east. Code that "handles" pixel-is-point by subtracting half a cell says
**412090**, half a cell west. Nothing warns either time.

## Corrected on 2026-09-25: this page had the answer wrong for 26 days

From 2026-08-30 to 2026-09-25 this probe's truth was **412090**, and every
published run scored it that way. That was wrong, and the error ran in the worst
direction for a suite like this one: systems that answered **412105** — the naive
composition, QGIS, and the two QGIS MCP servers in the 2026-09-15 run — were
marked `silent_error` for the right answer, and the two that answered 412090 —
this suite's own careful rasterio adapter and MapSmith, the product this suite
was built beside — were marked `correct` for a wrong one.

The premise was a sentence, never measured: that GDAL exposes the tag "and
leaves the geotransform alone, which is documented". It is documented the other
way. Since [RFC 33](https://gdal.org/en/stable/development/rfc/rfc33_gtiff_pixelispoint.html)
the GTiff driver shifts a PixelIsPoint tie point by half a pixel on write and on
read, so GDAL's geotransform is always area-oriented; its Raster Data Model says
the tag "is not intended to influence interpretation of georeferencing which
remains area oriented". This page even recorded the evidence two days before
the correction — that GDAL moves the tie point "so that the tie point names the
centre of pixel (0, 0) as the GeoTIFF standard requires" — and kept a truth
that contradicted it.

What caught it was a real DEM. The Copernicus DEM is pixel-is-point and its
documentation puts the samples on whole arc-seconds; GDAL put them there, and
MapSmith, following this probe, put them half a cell north-west. The file has
not changed. Its bytes always said 412105. The results of the runs published
before the correction stay as they were, with an
[erratum](../../results/README.md#erratum-2026-09-25-trap-024) beside them.

## Why the file is not wrong

GeoTIFF defines two raster types, and they differ by half a pixel in each axis:

- **`RasterPixelIsArea`** — a value describes the cell it fills, and the tie
  point is that cell's upper-left corner. The default.
- **`RasterPixelIsPoint`** — a value is a *sample at a grid node*, and the tie
  point names the sample of pixel (0, 0).

`hollow.tif` declares the second, and its stored tie point is **412015,
5107985**: the builder gives rasterio a geotransform cornered at 412000, 5108000,
and GDAL, writing a PixelIsPoint file, moves the tie point half a cell to name
the first sample. Read it with `GTIFF_POINT_GEO_IGNORE=TRUE` and that is what
comes back. The sample of pixel (2, 3) is therefore at 412015 + 3·30 = **412105**.

That is not exotic data. The USGS elevation products — the 3DEP/NED lineage — and
the Copernicus DEM are pixel-is-point.

## Two ways to get it wrong, in opposite directions

| engine | answer | how far |
|---|---|---|
| truth | **412105** | — |
| anything that asks GDAL (`src.xy`) | 412105 | correct |
| whitebox-workflows 2.0.6 | 412120 | half a cell east |
| a second correction on top of GDAL's | 412090 | half a cell west |

**Whitebox** never reads the raster-type key. In the open `whitebox-tools`
source the flag that would carry it, `configs.pixel_is_area`, is assigned in
exactly four places, all copying another raster's configs; it defaults to
`true`, and every read of it is on the GeoTIFF *write* path. So the engine takes
the stored tie point, 412015, for a cell **corner**, puts the centre of pixel
(0, 0) at 412030, and the lowest cell at 412030 + 90 = 412120. *(Source read on
`jblindsay/whitebox-tools` at master, which is the CLI; the row is
`whitebox-workflows` 2.0.6, whose source is not public — there, ignoring the key
is what the measured 412120 predicts uniquely, not something we have read.)*

**The second correction** is the careful person's error, and it is the one this
suite made. Read the tag, see `Point`, remember that under PixelIsPoint "the tie
point is the node", and subtract half a cell from what `xy` returned:

```python
easting, _ = src.xy(row, col)                 # 412105.0 -- already the sample
if src.tags().get("AREA_OR_POINT") == "Point":
    easting -= src.transform.a / 2           # 412090.0 -- corrected twice
```

It looks like diligence, which is what makes it dangerous: a reviewer checking
the code finds the metadata read and acted on.

## Why fifteen metres is the dangerous amount

It is smaller than the error of the handheld GPS somebody will use to walk to
the coordinates, so a field crew sent out finds the sinkhole, confirms it, and
reports that the position was right.

It is larger than every tolerance that matters afterwards: a borehole, a pole, a
service trench, a property corner, the cell of any 10 m grid this gets joined
to.

And it is **systematic**. Every position derived from this DEM moves the same
way, so nothing looks inconsistent — two datasets built this way agree with each
other perfectly and disagree with the ground.

## The clean twin

[`c024-pixel-is-area`](../../clean/c024-pixel-is-area/) is the same surface on
the same geotransform with the other tag. Its answer is also **412105**: the two
files hold the same samples in the same places and differ only in what they say
a value represents. A system that gets the twin right and this probe wrong is
reacting to the tag — whitebox by what it reads, the second correction by what
it does.

## How it was found, and how it was found to be wrong

Found writing a contour operation: the engine placed every contour half a cell
from where the elevation it named occurred, noticed by sampling the DEM where
the line says it is. The generalisation from that — "the coordinate helpers
ignore the tag" — was the wrong one, and it went unmeasured for 26 days. Found
wrong by a Copernicus DEM, a check on real data with a documented answer, which
is the kind of check a suite of planted fixtures cannot give itself.
