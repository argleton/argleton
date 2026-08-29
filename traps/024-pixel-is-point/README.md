# 024 — pixel is point

**A grid whose own metadata says its values sit at the nodes, read by every
coordinate helper as if they filled the cells.**

`hollow.tif` is an 8×8 digital elevation model at 30 m spacing, a shallow
depression with exactly one lowest cell. The question is where that cell is.

The right answer is an easting of **412090**. rasterio and a plain numpy
composition both say **412105**. Whitebox says **412120**. Nothing warns.

## Why the file is not wrong

GeoTIFF defines two raster types, and they differ by half a pixel in each axis:

- **`RasterPixelIsArea`** — a value describes the cell it fills, and the tie
  point is that cell's upper-left corner. The default, and what most data ships
  as.
- **`RasterPixelIsPoint`** — a value is a *sample at a grid node*, and the tie
  point is the node itself.

`hollow.tif` declares the second. That is not exotic: the USGS elevation
products — the 3DEP/NED lineage — are pixel-is-point, and so are many national
DEMs. GDAL reads the key faithfully and exposes it as the `AREA_OR_POINT`
metadata item, and its documentation is explicit that it does **not** adjust the
geotransform for it. The value is reported; the caller decides.

So the file is right, the library is right, and the position moves in the line
that joins them.

## The defect

```python
with rasterio.open(path) as src:
    values = src.read(1)
    row, col = np.unravel_index(np.argmin(values), values.shape)
    easting, northing = src.xy(row, col)      # 412105.0
```

`xy` returns the centre of the cell under the area reading, always. There is no
argument on it that mentions registration and nothing in its name suggests it
has taken a side.

The tag is one call away on the same object:

```python
src.tags()["AREA_OR_POINT"]                   # 'Point'
```

Same open dataset, same breath. The information survives all the way to the
caller and is discarded in the last line.

## Two engines, two different wrong answers

| engine | answer | how far |
|---|---|---|
| truth | 412090 | — |
| naive composition | 412105 | half a cell east |
| rasterio, carefully | 412105 | half a cell east |
| whitebox-workflows | 412120 | a *whole* cell east |

Whitebox is the interesting one. It reacts to the tag — its reported grid origin
shifts by half a cell on this file where it does not on the area-registered twin
— and the shift is in the direction that makes a caller who adds the usual half
cell for a centre land one full cell out. An engine that half-honours a
convention is worse than one that ignores it, because the correction that fixes
the second breaks on the first.

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

[`c024-pixel-is-area`](../../clean/c024-pixel-is-area/) is the same surface, the
same tie point, the same spacing, the same lowest node, and one different tag.
Its correct answer is **412105** — precisely the number that is wrong here.

That pairing is the point. A system that has learned about pixel-is-point and
now subtracts half a cell everywhere passes this trap and fails the twin. A
system that never heard of it passes the twin and fails this. Only one that
reads the tag answers both.

## How it was found

Writing a contour operation. The engine placed every contour half a cell from
where the elevation it named actually occurred, which was noticed by checking
the output against the input rather than by reading the documentation — sample
the DEM where the line says it is, and the elevation has to match. Asking how
far that generalised produced the raster-type key, and a convention that is
declared in the file, reported faithfully by every library, and honoured by none
of the coordinate helpers built on top of them.
